
import Packet as Pkt
import Global_Par as Gp
import time
from math import *

def takeSecond(elem):
    return elem[1]

def getdis(ax, ay, bx, by):
    temp_x = ax - bx
    temp_y = ay - by
    temp_x = temp_x * temp_x
    temp_y = temp_y * temp_y
    result = sqrt(temp_x+temp_y)
    return result
def angle(x0, y0, x1, y1, x2, y2):
    cos = ((x1-x0)*(x2-x0)+(y1-y0)*(y2-y0))/(sqrt(pow(x1-x0, 2)+pow(y1-y0, 2))*sqrt(pow(x2-x0, 2)+pow(y2-y0, 2)))
    theta = acos(cos)/pi
    return theta

class Node:
    def __init__(self, node_id, controller):
        self.node_id = node_id
        self.position = [0, 0, 0]
        self.velocity = [0, 0, 0]
        self.angle = 0
        self.acceleration = []
        self.routing_table = []
        self.hello_table = []
        self.neighbor_list = {}
        self.data_pkt_list = []
        self.test_data_pkt_list = []
        self.cache = 1024
        self.controller = controller
        self.pkt_seq = 0
        self.it_cover = {}
        self.area = []

    def update_node_position(self, node_id_position):
        self.velocity[0] = node_id_position[self.node_id][0, 0] - self.position[0]
        self.velocity[1] = node_id_position[self.node_id][0, 1] - self.position[1]
        self.velocity[2] = node_id_position[self.node_id][0, 2] - self.position[2]
        self.angle = angle(self.position[0], self.position[1], self.position[0], self.position[1]+1, node_id_position[self.node_id][0, 0],node_id_position[self.node_id][0, 1])
        self.position = [node_id_position[self.node_id][0, 0], node_id_position[self.node_id][0, 1], node_id_position[self.node_id][0, 2]]
        return

    def generate_hello_c(self, controller):
        controller.hello_list.append(Pkt.Hello_c(self.node_id,  self.position, self.cache))
        return

    def receive_notify(self, flow_notify):
        self.area = flow_notify.area
        return

    def generate_hello_n(self, node_list):
        for node in node_list:
            if self.node_id == node.node_id:
                continue
            d = getdis(self.position[0], self.position[1], node.position[0], node.position[1])
            if d < Gp.com_dis:
                node.hello_table.append(Pkt.Hello(self.node_id,  self.position, self.area, self.velocity,  self.acceleration,  self.cache))
        return


    def update_neighbor_list(self):
        self.neighbor_list = {}
        for pkt in self.hello_table:
            self.neighbor_list[pkt.node_id] = [pkt.position, pkt.area]
        self.hello_table = []
        return

    def generate_request(self, des_id, controller, size):
        print('node %d generate packet to node %d' % (self.node_id, des_id))
        self.pkt_seq = self.pkt_seq + 1
        self.data_pkt_list.append(Pkt.DataPkt(self.node_id, des_id, size, 0, self.node_id, self.pkt_seq, 1000 * time.time()))
        controller.flow_request_list.append(Pkt.FlowRequest(self.node_id, des_id, self.node_id, self.pkt_seq))
        return

    def generate_test_pkt(self, area_path, des_id):
        pkt = Pkt.DataPkt(self.node_id, des_id, 0, 0, self.node_id, self.pkt_seq, time.time())
        pkt.insert_info(area_path, 1)
        self.test_data_pkt_list.append(pkt)
        return

    def receive_test_flow(self, test_flow):
        self.generate_test_pkt(test_flow.area_path, test_flow.des_id)
        return

    def receive_flow(self, flow_reply):
        for pkt in self.data_pkt_list[::-1]:
            if pkt.source_id == self.node_id:
                pkt.insert_info(flow_reply.area_path, flow_reply.report_flag)
                break

    def forward_pkt(self, node_list, controller):
        for pkt in self.data_pkt_list[::-1]:
            if len(pkt.area_path) == 0:
                return
            next_hop, curr_area = self.find_next(pkt.des_id, pkt.area_path, node_list)
            if next_hop != -1:
                if next_hop in pkt.path:
                    pkt.count = 0
                    next_hop = -1
            if next_hop != -1:
                pkt.count += 1
                pkt.path.append(self.node_id)
                node_list[next_hop].receive_pkt(pkt, node_list, controller)
                return
            else:
                print("loss")
                Gp.fail_time += 1
                controller.flow_report_list.append(Pkt.FlowReport(pkt.area_path, 1, curr_area))
                return
        return

    def receive_pkt(self, data_pkt, node_list, controller):
        data_pkt.delay += 0.03
        if data_pkt.des_id == self.node_id:
            data_pkt.e_time = 1000 * time.time()
            data_pkt.delay = data_pkt.e_time - data_pkt.s_time
            dis_all = 0
            data_pkt.path.append(self.node_id)
            for i in range(0, len(data_pkt.path)-1):
                n1 = data_pkt.path[i]
                n2 = data_pkt.path[i+1]
                dis = getdis(node_list[n1].position[0], node_list[n1].position[1], node_list[n2].position[0], node_list[n2].position[1])
                dis_all += dis
            data_pkt.delay += dis_all * (0.005 / 1000) + data_pkt.count * 0.224
            Gp.pkt_delay.append(round(data_pkt.delay, 3))
            if Gp.delay_hop_tag == 800:
                Gp.pkt_delay_800.append(round(data_pkt.delay, 3))
            elif Gp.delay_hop_tag == 1600:
                Gp.pkt_delay_1600.append(round(data_pkt.delay, 3))
            elif Gp.delay_hop_tag == 2400:
                Gp.pkt_delay_2400.append(round(data_pkt.delay, 3))
            elif Gp.delay_hop_tag == 3200:
                Gp.pkt_delay_3200.append(round(data_pkt.delay, 3))

            dist = 0
            for i in range(0, len(data_pkt.path)-1):
                current = data_pkt.path[i]
                next = data_pkt.path[i+1]
                xc = node_list[current].position[0]
                yc = node_list[current].position[1]
                xn = node_list[next].position[0]
                yn = node_list[next].position[1]
                d = getdis(xc,yc,xn,yn)
                dist += d
            Gp.hop_list.append(dist)
            if Gp.delay_hop_tag == 800:
                Gp.hop_list_800.append(dist)
            elif Gp.delay_hop_tag == 1600:
                Gp.hop_list_1600.append(dist)
            elif Gp.delay_hop_tag == 2400:
                Gp.hop_list_2400.append(dist)
            elif Gp.delay_hop_tag == 3200:
                Gp.hop_list_3200.append(dist)
            print('%3d to %3d successful transmission！with delay = %3d ' % (data_pkt.source_id, data_pkt.des_id, Gp.pkt_delay[-1]))
            Gp.success_time += 1
            if data_pkt.report_flag == 1:
                controller.flow_report_list.append(Pkt.FlowReport(data_pkt.area_path, loss = 0, loss_area=0))
        else:
            self.data_pkt_list.append(data_pkt)
            self.forward_pkt(node_list, controller)
        return

    def forward_test_pkt(self, node_list, controller):
        for pkt in self.test_data_pkt_list[::-1]:
            if len(pkt.area_path) == 0:
                return
            next_hop, curr_area = self.find_next1(pkt.des_id, pkt.area_path, node_list)
            if next_hop != -1:
                if next_hop in pkt.path:
                    pkt.count = 0
                    next_hop = -1
            if next_hop != -1:
                pkt.count += 1
                pkt.path.append(self.node_id)
                node_list[next_hop].receive_test_pkt(pkt, node_list, controller)
                return
            else:
                return
        return

    def receive_test_pkt(self, data_pkt, node_list, controller):
        data_pkt.delay += 0.03
        if data_pkt.des_id == self.node_id:
            data_pkt.e_time = time.time()
            controller.flow_report_list.append(Pkt.FlowReport(data_pkt.area_path, loss=0, loss_area=0))
            Gp.test_success[-1] += 1
        else:
            self.test_data_pkt_list.append(data_pkt)
            self.forward_test_pkt(node_list, controller)
        return



    def link_stability(self, top_k, node_list):
        link_stability_record = []
        c_x = self.position[0]
        c_y = self.position[1]
        c_speed = getdis(self.velocity[0],0,self.velocity[1],0)
        for neib, info in self.neighbor_list.items():
            n_x = info[0][0]
            n_y = info[0][1]
            n_speed = getdis(node_list[neib].velocity[0],0,node_list[neib].velocity[1],0)
            speed_diff = abs(c_speed-n_speed) / 40
            distance = getdis(c_x, c_y, n_x, n_y)
            angle_difference = abs(self.angle - node_list[neib].angle)/pi
            link_stability_record.append(FLS.fuzzy_routing(1,1,1))
        next_hop = max(link_stability_record)
        next_hop = top_k[0]
        return next_hop

    def is_belong(self, area_set, area):
        for a in area_set:
            if a == area:
                return 1
        return 0


    def intra_area(self, des_id, destination, curr_area, node_list, k=0.3):
        next_hop = 0
        if des_id in self.neighbor_list.keys():
            next_hop = des_id
        else:
            closer_to_destination = []
            d1 = getdis(self.position[0], self.position[1], destination.position[0], destination.position[1])
            for neib_id, neib_info in self.neighbor_list.items():
                d2 = getdis(neib_info[0][0], neib_info[0][1], destination.position[0], destination.position[1])
                if d1 > d2:
                    if self.is_belong(neib_info[1], curr_area):
                        closer_to_destination.append((neib_id, d2))

            if closer_to_destination:
                top_k = []
                max_length = ceil(k * len(closer_to_destination))
                closer_to_destination.sort(key=takeSecond)
                for i in range(0, max_length):
                    top_k.append(closer_to_destination[i][0])
                    next_hop = self.link_stability(top_k, node_list)
            else:
                closer_to_current_area = []
                d3 = getdis(self.position[0], self.position[1], Gp.it_pos[curr_area][0], Gp.it_pos[curr_area][1])
                for neib_id, neib_info in self.neighbor_list.items():
                    d4 = getdis(neib_info[0][0], neib_info[0][1], Gp.it_pos[curr_area][0], Gp.it_pos[curr_area][1])
                    if d3 > d4:
                        if self.is_belong(neib_info[1], curr_area):
                            closer_to_current_area.append((neib_id, d4))

                if closer_to_current_area:
                    top_k = []
                    max_length = ceil(k * len(closer_to_current_area))
                    closer_to_current_area.sort(key=takeSecond)
                    for i in range(0, max_length):
                        top_k.append(closer_to_current_area[i][0])
                        next_hop = self.link_stability(top_k, node_list)
                else:
                    next_hop = -1
        return next_hop

    def inter_area(self, curr_area, next_area, node_list, k=0.3):
        next_hop = 0
        belong_to_next_area = []
        for neib_id, neib_info in self.neighbor_list.items():
            if next_area in neib_info[1]:
                d = getdis(neib_info[0][0], neib_info[0][1], Gp.it_pos[next_area][0],Gp.it_pos[next_area][1])
                belong_to_next_area.append((neib_id, d))
        if belong_to_next_area:
            top_k = []
            max_length = ceil(k * len(belong_to_next_area))
            belong_to_next_area.sort(key=takeSecond)
            for i in range(0,max_length):
                top_k.append(belong_to_next_area[i][0])
            next_hop = self.link_stability(top_k, node_list)
        else:
            closer_to_next_area = []
            d1 = getdis(self.position[0], self.position[1], Gp.it_pos[next_area][0], Gp.it_pos[next_area][1])
            for neib_id, neib_info in self.neighbor_list.items():
                d2 = getdis(neib_info[0][0], neib_info[0][1], Gp.it_pos[next_area][0], Gp.it_pos[next_area][1])
                if d1 > d2:
                    if self.is_belong(neib_info[1], curr_area):
                        closer_to_next_area.append((neib_id, d2))

            if closer_to_next_area:
                top_k = []
                max_length = ceil(k * len(closer_to_next_area))
                closer_to_next_area.sort(key=takeSecond)
                for i in range(0, max_length):
                    top_k.append(closer_to_next_area[i][0])
                next_hop = self.link_stability(top_k, node_list)
            else:
                closer_to_current_area = []
                d3 = getdis(self.position[0], self.position[1], Gp.it_pos[curr_area][0], Gp.it_pos[curr_area][1])
                for neib_id, neib_info in self.neighbor_list.items():
                    d4 = getdis(neib_info[0][0], neib_info[0][1], Gp.it_pos[curr_area][0], Gp.it_pos[curr_area][1])
                    if d3 > d4:
                        if self.is_belong(neib_info[1], curr_area):
                            closer_to_current_area.append((neib_id, d4))

                if closer_to_current_area:
                    top_k = []
                    max_length = ceil(k * len(closer_to_current_area))
                    closer_to_current_area.sort(key=takeSecond)
                    for i in range(0, max_length):
                        top_k.append(closer_to_current_area[i][0])
                    next_hop = self.link_stability(top_k, node_list)
                else:
                    next_hop = -1
        return next_hop

    def find_next(self, des_id, area_list, node_list):
        for a in self.area:
            for t in area_list:
                if a == t:
                    index =  area_list.index(t)
                    curr_area = a

        for a in self.area:
            if a == area_list[-1]:
                destination = node_list[des_id]
                next_hop = self.intra_area(des_id, destination, curr_area, node_list)
                return next_hop, curr_area
        next_area = area_list[index + 1]
        next_hop = self.inter_area(curr_area, next_area, node_list)
        return next_hop, curr_area

    def intra_area1(self, des_id, destination, curr_area, k=0.3):
        next_hop = 0
        if des_id in self.neighbor_list.keys():
            next_hop = des_id
        else:
            closer_to_destination = []
            d1 = getdis(self.position[0], self.position[1], destination.position[0], destination.position[1])
            for neib_id, neib_info in self.neighbor_list.items():
                d2 = getdis(neib_info[0][0], neib_info[0][1], destination.position[0], destination.position[1])
                if d1 > d2:
                    if self.is_belong(neib_info[1], curr_area):
                        closer_to_destination.append((neib_id, d2))

            if closer_to_destination:
                top_k = []
                max_length = ceil(k * len(closer_to_destination))
                closer_to_destination.sort(key=takeSecond)
                for i in range(0, max_length):
                    top_k.append(closer_to_destination[i][0])
                    next_hop = top_k[0]
            else:
                closer_to_current_area = []
                d3 = getdis(self.position[0], self.position[1], Gp.it_pos[curr_area][0], Gp.it_pos[curr_area][1])
                for neib_id, neib_info in self.neighbor_list.items():
                    d4 = getdis(neib_info[0][0], neib_info[0][1], Gp.it_pos[curr_area][0], Gp.it_pos[curr_area][1])
                    if d3 > d4:
                        if self.is_belong(neib_info[1], curr_area):
                            closer_to_current_area.append((neib_id, d4))
                if closer_to_current_area:
                    top_k = []
                    max_length = ceil(k * len(closer_to_current_area))
                    closer_to_current_area.sort(key=takeSecond)
                    for i in range(0, max_length):
                        top_k.append(closer_to_current_area[i][0])
                        next_hop = top_k[0]
                else:
                    next_hop = -1
        return next_hop

    def inter_area1(self, curr_area, next_area, k=0.3):
        next_hop = 0
        belong_to_next_area = []
        for neib_id, neib_info in self.neighbor_list.items():
            if next_area in neib_info[1]:
                d = getdis(neib_info[0][0], neib_info[0][1], Gp.it_pos[next_area][0], Gp.it_pos[next_area][1])
                belong_to_next_area.append((neib_id, d))
        if belong_to_next_area:
            top_k = []
            max_length = ceil(k * len(belong_to_next_area))
            belong_to_next_area.sort(key=takeSecond)
            for i in range(0, max_length):
                top_k.append(belong_to_next_area[i][0])
            next_hop = top_k[0]
        else:
            closer_to_next_area = []
            d1 = getdis(self.position[0], self.position[1], Gp.it_pos[next_area][0], Gp.it_pos[next_area][1])
            for neib_id, neib_info in self.neighbor_list.items():
                d2 = getdis(neib_info[0][0], neib_info[0][1], Gp.it_pos[next_area][0], Gp.it_pos[next_area][1])
                if d1 > d2:
                    if self.is_belong(neib_info[1], curr_area):
                        closer_to_next_area.append((neib_id, d2))

            if closer_to_next_area:
                top_k = []
                max_length = ceil(k * len(closer_to_next_area))
                closer_to_next_area.sort(key=takeSecond)
                for i in range(0, max_length):
                    top_k.append(closer_to_next_area[i][0])
                next_hop = top_k[0]
            else:
                closer_to_current_area = []
                d3 = getdis(self.position[0], self.position[1], Gp.it_pos[curr_area][0], Gp.it_pos[curr_area][1])
                for neib_id, neib_info in self.neighbor_list.items():
                    d4 = getdis(neib_info[0][0], neib_info[0][1], Gp.it_pos[curr_area][0], Gp.it_pos[curr_area][1])
                    if d3 > d4:
                        if self.is_belong(neib_info[1], curr_area):
                            closer_to_current_area.append((neib_id, d4))

                if closer_to_current_area:
                    top_k = []
                    max_length = ceil(k * len(closer_to_current_area))
                    closer_to_current_area.sort(key=takeSecond)
                    for i in range(0, max_length):
                        top_k.append(closer_to_current_area[i][0])
                    next_hop = top_k[0]
                else:
                    next_hop = -1
        return next_hop

    def find_next1(self, des_id, area_list, node_list):
        for a in self.area:
            for t in area_list:
                if a == t:
                    index = area_list.index(t)
                    curr_area = a
        for a in self.area:
            if a == area_list[-1]:
                destination = node_list[des_id]
                next_hop = self.intra_area1(des_id, destination, curr_area)
                return next_hop, curr_area
        next_area = area_list[index + 1]
        next_hop = self.inter_area1(curr_area, next_area)
        return next_hop, curr_area