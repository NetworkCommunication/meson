import time
class Hello:
    def __init__(self, node_id, position, area, velocity, acceleration, current_cache):
        self.node_id = node_id
        self.position = position
        self.area = area
        self.velocity = velocity
        self.acceleration = acceleration
        self.current_cache = current_cache

class Hello_c:
    def __init__(self, node_id, position, current_cache):
        self.node_id = node_id
        self.position = position
        self.current_cache = current_cache

class FlowRequest:
    def __init__(self, source_id, des_id, node_id, seq):
        self.source_id = source_id
        self.des_id = des_id
        self.seq = seq
        self.node_id = node_id

class FlowReply:
    def __init__(self, area_path, report_flag):
        self.area_path = area_path
        self.report_flag = report_flag

class FlowTest:
    def __init__(self, area_path, des_id):
        self.area_path = area_path
        self.des_id = des_id

class FlowNotify:
    def __init__(self, area):
        self.area = area # []


class FlowReport:
    def __init__(self, area_path, loss, loss_area):
        self.area_path = area_path
        self.loss = loss
        self.loss_area = loss_area

class FlowError:
    def __init__(self, source_id, des_id, error_id, time, source_seq, error_seq):
        self.source_id = source_id
        self.des_id = des_id
        self.error_id = error_id
        self.time = time
        self.source_seq = source_seq
        self.error_seq = error_seq

class DataPkt:
    def __init__(self, source_id, des_id, pkt_size, state, node_id, seq, s_time):
        self.source_id = source_id
        self.des_id = des_id
        self.pkt_size = pkt_size
        self.state = state
        self.seq = seq
        self.node_id = node_id
        self.s_time = s_time
        self.initial_intersection = 0
        self.target_intersection = 0
        self.path = [] #
        self.last_area = -1
        self.area_path = []
        self.e_time = 0
        self.delay = 0
        self.count = 0
        self.report_flag = 0

    def insert_info(self, area_path, report_flag):
        self.area_path = area_path
        self.report_flag = report_flag

    def update1(self, s_belong_it, d_belong_it):
        self.initial_intersection = s_belong_it
        self.target_intersection = d_belong_it

