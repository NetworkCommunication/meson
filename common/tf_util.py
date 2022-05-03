import joblib
import numpy as np
import tensorflow as tf  # pylint: ignore-module
import copy
import os
import functools
import collections
import multiprocessing

def switch(condition, then_expression, else_expression):
    x_shape = copy.copy(then_expression.get_shape())
    x = tf.cond(tf.cast(condition, 'bool'),
                lambda: then_expression,
                lambda: else_expression)
    x.set_shape(x_shape)
    return x

def lrelu(x, leak=0.2):
    f1 = 0.5 * (1 + leak)
    f2 = 0.5 * (1 - leak)
    return f1 * x + f2 * abs(x)

def huber_loss(x, delta=1.0):
    """Reference: https://en.wikipedia.org/wiki/Huber_loss"""
    return tf.where(
        tf.abs(x) < delta,
        tf.square(x) * 0.5,
        delta * (tf.abs(x) - 0.5 * delta)
    )

def get_session(config=None):
    sess = tf.get_default_session()
    if sess is None:
        sess = make_session(config=config, make_default=True)
    return sess

def make_session(config=None, num_cpu=None, make_default=False, graph=None):
    if num_cpu is None:
        num_cpu = int(os.getenv('RCALL_NUM_CPU', multiprocessing.cpu_count()))
    if config is None:
        config = tf.ConfigProto(
            allow_soft_placement=True,
            inter_op_parallelism_threads=num_cpu,
            intra_op_parallelism_threads=num_cpu)
        config.gpu_options.allow_growth = True

    if make_default:
        return tf.InteractiveSession(config=config, graph=graph)
    else:
        return tf.Session(config=config, graph=graph)

def single_threaded_session():
    return make_session(num_cpu=1)

def in_session(f):
    @functools.wraps(f)
    def newfunc(*args, **kwargs):
        with tf.Session():
            f(*args, **kwargs)
    return newfunc

ALREADY_INITIALIZED = set()

def initialize():
    new_variables = set(tf.global_variables()) - ALREADY_INITIALIZED
    get_session().run(tf.variables_initializer(new_variables))
    ALREADY_INITIALIZED.update(new_variables)

def normc_initializer(std=1.0, axis=0):
    def _initializer(shape, dtype=None, partition_info=None):  # pylint: disable=W0613
        out = np.random.randn(*shape).astype(dtype.as_numpy_dtype)
        out *= std / np.sqrt(np.square(out).sum(axis=axis, keepdims=True))
        return tf.constant(out)
    return _initializer

def conv2d(x, num_filters, name, filter_size=(3, 3), stride=(1, 1), pad="SAME", dtype=tf.float32, collections=None,
           summary_tag=None):
    with tf.variable_scope(name):
        stride_shape = [1, stride[0], stride[1], 1]
        filter_shape = [filter_size[0], filter_size[1], int(x.get_shape()[3]), num_filters]
        fan_in = intprod(filter_shape[:3])
        fan_out = intprod(filter_shape[:2]) * num_filters
        w_bound = np.sqrt(6. / (fan_in + fan_out))
        w = tf.get_variable("W", filter_shape, dtype, tf.random_uniform_initializer(-w_bound, w_bound),
                            collections=collections)
        b = tf.get_variable("b", [1, 1, 1, num_filters], initializer=tf.zeros_initializer(),
                            collections=collections)
        if summary_tag is not None:
            tf.summary.image(summary_tag,
                             tf.transpose(tf.reshape(w, [filter_size[0], filter_size[1], -1, 1]),
                                          [2, 0, 1, 3]),
                             max_images=10)

        return tf.nn.conv2d(x, w, stride_shape, pad) + b

def function(inputs, outputs, updates=None, givens=None):
    if isinstance(outputs, list):
        return _Function(inputs, outputs, updates, givens=givens)
    elif isinstance(outputs, (dict, collections.OrderedDict)):
        f = _Function(inputs, outputs.values(), updates, givens=givens)
        return lambda *args, **kwargs: type(outputs)(zip(outputs.keys(), f(*args, **kwargs)))
    else:
        f = _Function(inputs, [outputs], updates, givens=givens)
        return lambda *args, **kwargs: f(*args, **kwargs)[0]


class _Function(object):
    def __init__(self, inputs, outputs, updates, givens):
        for inpt in inputs:
            if not hasattr(inpt, 'make_feed_dict') and not (type(inpt) is tf.Tensor and len(inpt.op.inputs) == 0):
                assert False, "inputs should all be placeholders, constants, or have a make_feed_dict method"
        self.inputs = inputs
        updates = updates or []
        self.update_group = tf.group(*updates)
        self.outputs_update = list(outputs) + [self.update_group]
        self.givens = {} if givens is None else givens

    def _feed_input(self, feed_dict, inpt, value):
        if hasattr(inpt, 'make_feed_dict'):
            feed_dict.update(inpt.make_feed_dict(value))
        else:
            feed_dict[inpt] = adjust_shape(inpt, value)

    def __call__(self, *args):
        assert len(args) <= len(self.inputs), "Too many arguments provided"
        feed_dict = {}
        # Update the args
        for inpt, value in zip(self.inputs, args):
            self._feed_input(feed_dict, inpt, value)
        # Update feed dict with givens.
        for inpt in self.givens:
            feed_dict[inpt] = adjust_shape(inpt, feed_dict.get(inpt, self.givens[inpt]))
        results = get_session().run(self.outputs_update, feed_dict=feed_dict)[:-1]
        return results


def var_shape(x):
    out = x.get_shape().as_list()
    assert all(isinstance(a, int) for a in out), \
        "shape function assumes that shape is fully known"
    return out

def numel(x):
    return intprod(var_shape(x))

def intprod(x):
    return int(np.prod(x))

def flatgrad(loss, var_list, clip_norm=None):
    grads = tf.gradients(loss, var_list)
    if clip_norm is not None:
        grads = [tf.clip_by_norm(grad, clip_norm=clip_norm) for grad in grads]
    return tf.concat(axis=0, values=[
        tf.reshape(grad if grad is not None else tf.zeros_like(v), [numel(v)])
        for (v, grad) in zip(var_list, grads)
    ])

class SetFromFlat(object):
    def __init__(self, var_list, dtype=tf.float32):
        assigns = []
        shapes = list(map(var_shape, var_list))
        total_size = np.sum([intprod(shape) for shape in shapes])

        self.theta = theta = tf.placeholder(dtype, [total_size])
        start = 0
        assigns = []
        for (shape, v) in zip(shapes, var_list):
            size = intprod(shape)
            assigns.append(tf.assign(v, tf.reshape(theta[start:start + size], shape)))
            start += size
        self.op = tf.group(*assigns)

    def __call__(self, theta):
        tf.get_default_session().run(self.op, feed_dict={self.theta: theta})

class GetFlat(object):
    def __init__(self, var_list):
        self.op = tf.concat(axis=0, values=[tf.reshape(v, [numel(v)]) for v in var_list])

    def __call__(self):
        return tf.get_default_session().run(self.op)

def flattenallbut0(x):
    return tf.reshape(x, [-1, intprod(x.get_shape().as_list()[1:])])


_PLACEHOLDER_CACHE = {}  # name -> (placeholder, dtype, shape)

def get_placeholder(name, dtype, shape):
    if name in _PLACEHOLDER_CACHE:
        out, dtype1, shape1 = _PLACEHOLDER_CACHE[name]
        if out.graph == tf.get_default_graph():
            assert dtype1 == dtype and shape1 == shape, \
                'Placeholder with name {} has already been registered and has shape {}, different from requested {}'.format(name, shape1, shape)
            return out

    out = tf.placeholder(dtype=dtype, shape=shape, name=name)
    _PLACEHOLDER_CACHE[name] = (out, dtype, shape)
    return out

def get_placeholder_cached(name):
    return _PLACEHOLDER_CACHE[name][0]





def display_var_info(vars):
    import logger
    count_params = 0
    for v in vars:
        name = v.name
        if "/Adam" in name or "beta1_power" in name or "beta2_power" in name: continue
        v_params = np.prod(v.shape.as_list())
        count_params += v_params
        if "/b:" in name or "/bias" in name: continue    # Wx+b, bias is not interesting to look at => count params, but not print
        logger.info("   %s%s %i params %s" % (name, " "*(55-len(name)), v_params, str(v.shape)))

    logger.info("Total model parameters: %0.2f million" % (count_params*1e-6))


def get_available_gpus():


    from tensorflow.python.client import device_lib
    local_device_protos = device_lib.list_local_devices()
    return [x.name for x in local_device_protos if x.device_type == 'GPU']

# ================================================================
# Saving variables
# ================================================================

def load_state(fname, sess=None):
    import logger
    logger.warn('load_state method is deprecated, please use load_variables instead')
    sess = sess or get_session()
    saver = tf.train.Saver()
    saver.restore(tf.get_default_session(), fname)

def save_state(fname, sess=None):
    import logger
    logger.warn('save_state method is deprecated, please use save_variables instead')
    sess = sess or get_session()
    dirname = os.path.dirname(fname)
    if any(dirname):
        os.makedirs(dirname, exist_ok=True)
    saver = tf.train.Saver()
    saver.save(tf.get_default_session(), fname)

# The methods above and below are clearly doing the same thing, and in a rather similar way

def save_variables(save_path, variables=None, sess=None):
    sess = sess or get_session()
    variables = variables or tf.trainable_variables()

    ps = sess.run(variables)
    save_dict = {v.name: value for v, value in zip(variables, ps)}
    dirname = os.path.dirname(save_path)
    if any(dirname):
        os.makedirs(dirname, exist_ok=True)
    joblib.dump(save_dict, save_path)

def load_variables(load_path, variables=None, sess=None):
    sess = sess or get_session()
    variables = variables or tf.trainable_variables()

    loaded_params = joblib.load(os.path.expanduser(load_path))
    restores = []
    if isinstance(loaded_params, list):
        assert len(loaded_params) == len(variables), 'number of variables loaded mismatches len(variables)'
        for d, v in zip(loaded_params, variables):
            restores.append(v.assign(d))
    else:
        for v in variables:
            restores.append(v.assign(loaded_params[v.name]))

    sess.run(restores)

def adjust_shape(placeholder, data):
    if not isinstance(data, np.ndarray) and not isinstance(data, list):
        return data
    if isinstance(data, list):
        data = np.array(data)

    placeholder_shape = [x or -1 for x in placeholder.shape.as_list()]

    assert _check_shape(placeholder_shape, data.shape), \
        'Shape of data {} is not compatible with shape of the placeholder {}'.format(data.shape, placeholder_shape)

    return np.reshape(data, placeholder_shape)


def _check_shape(placeholder_shape, data_shape):

    squeezed_placeholder_shape = _squeeze_shape(placeholder_shape)
    squeezed_data_shape = _squeeze_shape(data_shape)

    for i, s_data in enumerate(squeezed_data_shape):
        s_placeholder = squeezed_placeholder_shape[i]
        if s_placeholder != -1 and s_data != s_placeholder:
            return False

    return True


def _squeeze_shape(shape):
    return [x for x in shape if x != 1]



def launch_tensorboard_in_background(log_dir):
    import subprocess
    subprocess.Popen(['tensorboard', '--logdir', log_dir])
