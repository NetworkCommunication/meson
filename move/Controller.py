import Packet as Pkt
import Global_Par as Gp
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import random

class SDVNController:
    def __init__(self, node_num, intersection):
        self.hello_list = []
        self.flow_request_list = []
        self.flow_report_list = []
        self.intersection = intersection
        self.node_info_dict = {i: [] for i in range(node_num)}
        self.all_node_neighbor = {i: [] for i in range(node_num)}
        self.it_cover = {i: -1 for i in range(node_num)}
        self.routing_table = RT.Routing_Table(intersection)
        self.inter_vehicles_number = {}
        self.intra_vehicles_number = {}
        self.intra_vehicles_detail = {}
        self.path_length = {}
        self.part_length = {}


    def fresh_routing_table(self):
        self.routing_table.strength = {current: {target: 0 for target in self.intersection} for current in self.intersection}
        return


    def predict_position(self):
        for value in self.hello_list:
            self.node_info_dict[value.node_id] = [value.position, value.current_cache]
        self.hello_list.clear()
        return


    def send_area_info(self, node_list):
        for node in node_list:
            area = self.it_cover[node.node_id]
            flow_notify = Pkt.FlowNotify(area)
            node.receive_notify(flow_notify)
        return

    def area_greedy(self, node_area, des_area):
        area_path = []
        d_x = Gp.it_pos[des_area][0]
        d_y = Gp.it_pos[des_area][1]
        current = node_area
        area_path.append(current)
        while current != des_area:
            min_ = 9999
            min_neib = -1
            for neib in Gp.adjacents_comb[current]:
                n_x = Gp.it_pos[neib][0]
                n_y = Gp.it_pos[neib][1]
                d = Exact.getdis(n_x, n_y, d_x, d_y)
                if d < min_:
                    min_ = d
                    min_neib = neib
            if min_neib != -1 and min_neib not in area_path:
                area_path.append(min_neib)
                current = min_neib
            else:
                area_path = []
                break
        return area_path

    def calculate_area_path(self, node_id, des_id):
        area_path = []
        node_area = self.it_cover[node_id][0]
        des_area = self.it_cover[des_id][0]
        current_area = node_area
        area_path.append(current_area)
        while current_area != des_area:
            if des_area in Gp.adjacents_comb[current_area]:
                area_path.append(des_area)
                break
            candidates_dict = self.routing_table.table[current_area][des_area]
            candidates = sorted(candidates_dict.items(), key=lambda item:item[1], reverse=True)
            if candidates[0][0] not in area_path:
                area_path.append(candidates[0][0])
                current_area = candidates[0][0]
            else:
                print("loop in area selection")
                Gp.loop_fail_time += 1
                area_path = []
                return area_path
        i = 0
        for area in area_path:
            if node_id in self.intra_vehicles_detail[area] and area != node_area:
                i = area_path.index(area)
        area_path = area_path[i:]
        print("area path: ", area_path)
        return area_path


    def calculate_test_area_path(self, node_id, des_id):
        area_path = []
        node_area = self.it_cover[node_id][0]
        des_area = self.it_cover[des_id][0]
        current_area = node_area
        area_path.append(current_area)
        while current_area != des_area:
            if des_area in Gp.adjacents_comb[current_area]:
                area_path.append(des_area)
                break
            candidates_dict = self.routing_table.table[current_area][des_area]
            candidates = sorted(candidates_dict.items(), key=lambda item: item[1], reverse=True)
            if current_area == node_area:
                if len(candidates) <= 1:
                    area_path = []
                    return area_path
                else:
                    can = []
                    for i in range(1, len(candidates)):
                        if candidates[i][0] not in area_path:
                            # print(candidates[i][0])
                            can.append(candidates[i][0])
                    if can:
                        next_area = random.choice(can)
                        area_path.append(next_area)
                        current_area = next_area
                    else:
                        #print("loop in area selection")
                        Gp.test_loop_fail_time += 1
                        area_path = []
                        return area_path
            else:
                if candidates[0][0] not in area_path:
                    area_path.append(candidates[0][0])
                    current_area = candidates[0][0]
                else:
                    #print("loop in area selection")
                    Gp.test_loop_fail_time += 1
                    area_path = []
                    return area_path
        return area_path


    def send_test_request(self, node_list, source_area, target_area):

        if self.intra_vehicles_detail[source_area] and self.intra_vehicles_detail[target_area]:
            source_id = random.choice(self.intra_vehicles_detail[source_area])
            target_id = random.choice(self.intra_vehicles_detail[target_area])
        else:
            return -1

        area_path = self.calculate_test_area_path(source_id, target_id)

        if not area_path:
            return -2
        test_flow = Pkt.FlowTest(area_path, target_id)
        for node in node_list:
            if node.node_id == source_id:
                node.receive_test_flow(test_flow)
        return source_id

    def send_reply(self, requester_id, area_path, node_list, report_flag):
        flow_reply = Pkt.FlowReply(area_path, report_flag)
        for node in node_list:
            if node.node_id == requester_id:
                node.receive_flow(flow_reply)
        return

    def resolve_request(self, node_list):
        for request in self.flow_request_list:
            area_path = self.calculate_area_path(request.node_id, request.des_id)
            source_area = self.it_cover[request.node_id][0]
            des_area = self.it_cover[request.des_id][0]
            if self.routing_table.strength[source_area][des_area] > 0:
                report_flag = 0
            else:
                report_flag = 1
            self.send_reply(request.node_id, area_path, node_list, report_flag)
        self.flow_request_list.clear()
        return

    def analyze(self):

        veh_num, veh_detail, path_length, node_area = rntf.intra_vehicles_num(self.node_info_dict, Gp.it_pos, Gp.adjacents_comb)
        part_veh_num, part_length = rntf.inter_vehicles_num(self.node_info_dict, Gp.it_pos, Gp.adjacents_comb)
        self.path_length = path_length
        self.intra_vehicles_detail = veh_detail
        self.intra_vehicles_number = veh_num
        self.it_cover = node_area
        self.part_length = part_length
        self.inter_vehicles_number = part_veh_num
        return

    def init_routing_table(self):
        self.routing_table.initial(self.intra_vehicles_number, self.path_length, self.inter_vehicles_number, self.part_length)
        return

    def update_routing_table(self, area_path, loss, loss_area, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length):

        if loss == 0:
            self.routing_table.positive_update(area_path, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length)

        elif loss == 1:
            if len(area_path) == 1:
                print("单个区域内部传输，并出错1！")
            self.routing_table.negative_update1(area_path, loss_area, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length)
        elif loss == 2:
            if len(area_path) == 1:
                print("单个区域内部传输，并出错2！")
            self.routing_table.negative_update2(area_path, loss_area)
        return


    def resolve_report(self):
        for report in self.flow_report_list:
            self.update_routing_table(report.area_path, report.loss, report.loss_area, self.intra_vehicles_number,
                                      self.path_length, self.inter_vehicles_number, self.part_length)

        Gp.overhead[Gp.overhead_index] += len(self.flow_report_list)
        self.flow_report_list = []
        return
