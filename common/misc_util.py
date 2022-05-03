import gym
import numpy as np
import os
import pickle
import random
import tempfile
import zipfile

def zipsame(*seqs):
    L = len(seqs[0])
    assert all(len(seq) == L for seq in seqs[1:])
    return zip(*seqs)


def unpack(seq, sizes):
    seq = list(seq)
    it = iter(seq)
    assert sum(1 if s is None else s for s in sizes) == len(seq), "Trying to unpack %s into %s" % (seq, sizes)
    for size in sizes:
        if size is None:
            yield it.__next__()
        else:
            li = []
            for _ in range(size):
                li.append(it.__next__())
            yield li


class EzPickle(object):
    def __init__(self, *args, **kwargs):
        self._ezpickle_args = args
        self._ezpickle_kwargs = kwargs

    def __getstate__(self):
        return {"_ezpickle_args": self._ezpickle_args, "_ezpickle_kwargs": self._ezpickle_kwargs}

    def __setstate__(self, d):
        out = type(self)(*d["_ezpickle_args"], **d["_ezpickle_kwargs"])
        self.__dict__.update(out.__dict__)


def set_global_seeds(i):
    try:
        import tensorflow as tf
    except ImportError:
        pass
    else:
        tf.set_random_seed(i)
    np.random.seed(i)
    random.seed(i)


def pretty_eta(seconds_left):
    minutes_left = seconds_left // 60
    seconds_left %= 60
    hours_left = minutes_left // 60
    minutes_left %= 60
    days_left = hours_left // 24
    hours_left %= 24

    def helper(cnt, name):
        return "{} {}{}".format(str(cnt), name, ('s' if cnt > 1 else ''))

    if days_left > 0:
        msg = helper(days_left, 'day')
        if hours_left > 0:
            msg += ' and ' + helper(hours_left, 'hour')
        return msg
    if hours_left > 0:
        msg = helper(hours_left, 'hour')
        if minutes_left > 0:
            msg += ' and ' + helper(minutes_left, 'minute')
        return msg
    if minutes_left > 0:
        return helper(minutes_left, 'minute')
    return 'less than a minute'


class RunningAvg(object):
    def __init__(self, gamma, init_value=None):
        self._value = init_value
        self._gamma = gamma

    def update(self, new_val):
        if self._value is None:
            self._value = new_val
        else:
            self._value = self._gamma * self._value + (1.0 - self._gamma) * new_val

    def __float__(self):

        return self._value

def boolean_flag(parser, name, default=False, help=None):
    dest = name.replace('-', '_')
    parser.add_argument("--" + name, action="store_true", default=default, dest=dest, help=help)
    parser.add_argument("--no-" + name, action="store_false", dest=dest)


def get_wrapper_by_name(env, classname):
    currentenv = env
    while True:
        if classname == currentenv.class_name():
            return currentenv
        elif isinstance(currentenv, gym.Wrapper):
            currentenv = currentenv.env
        else:
            raise ValueError("Couldn't find wrapper named %s" % classname)


def relatively_safe_pickle_dump(obj, path, compression=False):
    temp_storage = path + ".relatively_safe"
    if compression:
        # Using gzip here would be simpler, but the size is limited to 2GB
        with tempfile.NamedTemporaryFile() as uncompressed_file:
            pickle.dump(obj, uncompressed_file)
            uncompressed_file.file.flush()
            with zipfile.ZipFile(temp_storage, "w", compression=zipfile.ZIP_DEFLATED) as myzip:
                myzip.write(uncompressed_file.name, "data")
    else:
        with open(temp_storage, "wb") as f:
            pickle.dump(obj, f)
    os.rename(temp_storage, path)


def pickle_load(path, compression=False):
    if compression:
        with zipfile.ZipFile(path, "r", compression=zipfile.ZIP_DEFLATED) as myzip:
            with myzip.open("data") as f:
                return pickle.load(f)
    else:
        with open(path, "rb") as f:
            return pickle.load(f)
