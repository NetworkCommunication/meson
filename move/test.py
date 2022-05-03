import Get_Move as Gm
import Init
import numpy as np
import pandas as pd
import Global_Par as Gp
import time as t
import road_network_traffic_file_analysis as rntfa
import math
import matplotlib.pyplot as plt
import random
import openpyxl
import xlwt
from math import *
node_list = [] # 所有节点
com_node_list = [] # 通信的节点
begin_time = 200 # 仿真开始时间
sim_time = 300 # 仿真结束阈值
valid_nodes_num = [] # 有效节点数

# 距离
def getdis(ax, ay, bx, by):
    temp_x = ax - bx
    temp_y = ay - by
    temp_x = temp_x * temp_x
    temp_y = temp_y * temp_y
    result = sqrt(temp_x+temp_y)
    return result

if __name__ == '__main__':
    # 选择移动文件
    for u in [5]:#[0,1,2,3,5]:#[2,4,6,8,10]:#[3,3,3,3,3]:#[3,2,1,0,3,2,1,0,4,4,4,4]:
        Gp.nor_para_seq = u
        if u==0:
            movement_file = "tiexi-500.mobility.tcl" #  400 14p/s
            pkt_num = 16
        elif u==1:
            movement_file = "tiexi-1000.mobility.tcl" # 800 27p/s
            pkt_num = 24
        elif u==2:
            movement_file = "tiexi-1500.mobility.tcl" # 1200 40p/s
            pkt_num = 40
        elif u==3:
            movement_file = "tiexi-2000.mobility.tcl" # 1600 54p/s
            pkt_num = 56
        elif u == 4:
            movement_file = "tiexi-2500.mobility.tcl"  # 2000 67p/s
            pkt_num = 68
        elif u==5:
            movement_file = "tiexi-3000.mobility.tcl" # 2400 80p/s
            pkt_num = 80
        elif u==6:
            movement_file = "tiexi-4000.mobility.tcl" # 3200 107p/s
            pkt_num = 108
        elif u==7:
            movement_file = "tiexi-5000.mobility.tcl" # 4000 134p/s
            pkt_num = 136
        else:
            print('wrong~')
            movement_file = 'tiexi-1000.mobility.tcl'
            pkt_num = 24
        # 位置文件读取
        # get_position()获取“车辆运动轨迹，车辆节点初始位置”
        # 其中，“车辆运动轨迹”为一个矩阵，每一行元素分别为“时间，id，x，y，z”；“车辆节点初始位置”为一个矩阵，每一行元素为“id，x，y”
        print("get movement...")
        movement_matrix, init_position_matrix = Gm.get_position(movement_file)
        node_num = init_position_matrix.shape[0] # 矩阵第一维的数量（行数），表示车辆节点数量

        # 位置数据处理
        # 对车辆节点初始位置矩阵进行处理：按照第一列（id）的顺序进行排序
        init_position_arranged = init_position_matrix[np.lexsort(init_position_matrix[:, ::-1].T)]
        node_position = init_position_arranged[0]

        # 路口 {it_1:[x,y], it_2:[x,y], ..., it_n:[x,y]}
        #Gp.intersection = Init.observe_intersection('z_intersection.xml')
        Gp.intersection = rntfa.junction()
        Gp.edges_boundary = rntfa.edge()
        Gp.adjacents= rntfa.adjacent(Gp.edges_boundary, Gp.intersection)
        rntfa.intersection_combination(Gp.intersection) # intersections_combination：[[],[],...]
        rntfa.combination() # it_pos
        rntfa.comb_adjacent() # adjacents_comb

        # 处理，把所有的边缘路口在路口集合中删除，并在邻居关系中全部删除
        for un_it in Gp.un_intersections:
            del Gp.it_pos[un_it] # 在路口字典中删除无效（边缘）路口
            del Gp.adjacents_comb[un_it] # 在邻居字典中删除无效（边缘）路口
        for it, neibs in Gp.adjacents_comb.items():
            for un_it in Gp.un_intersections:
                if un_it in neibs: # 无效（边缘）路口如果在邻居字典中，就删掉
                    Gp.adjacents_comb[it].remove(un_it)

        # 远距离邻居
        un = {}
        for it, neibs in Gp.adjacents_comb.items():
            for neib in neibs: # 直接根据距离删除这些
                current_x = Gp.it_pos[it][0]
                current_y = Gp.it_pos[it][1]
                neib_x = Gp.it_pos[neib][0]
                neib_y = Gp.it_pos[neib][1]
                # 分别计算c-t和a-t的距离
                dis = getdis(current_x, current_y, neib_x, neib_y)  # 当前区域到目的区域的距离
                if dis > 800:
                    un[it] = neib
        for it, neb in un.items():
            Gp.adjacents_comb[it].remove(neb)

        print("intersections: ", Gp.it_pos)
        print("adjacency: ", Gp.adjacents_comb)
        print("number of intersections: ", len(Gp.it_pos))

        # 控制器初始化
        controller = Init.init_controller(node_num, Gp.it_pos)

        # 节点初始化，获得车辆节点列表node_list，列表中每一个元素代表一个节点,具有自己的id
        node_list = (Init.init_node(node_position, controller))

        # 计算时间，时延，抖动初始化
        effi = 0
        delay = 0
        std2 = 0

        # 多次训练
        for x in range(0,3):
            if x == 0:
                Gp.overhead = [0 for i in range(0,sim_time-begin_time)]
            controller.fresh_routing_table() # 清空路由表内容
            start_time = t.time() # 获取开始时间
            # 在begin_time到sim_time时间段内仿真
            for time in range(begin_time, sim_time): #sim_time
            #for time in range(450, 451):
                print('\nTime: %d'% time) # 打印当前时刻（200-sim_time）
                Gp.overhead_index = time-begin_time
                # np.nonzero()返回数组中非零元素的索引值数组
                # .A 将矩阵转化为数组类型
                # 这里是将“车辆运动轨迹”中时间为当前time的所有行取出存放到current_move中 （==time 为 true）
                current_move = movement_matrix[np.nonzero(movement_matrix[:, 0].A == time)[0], :]
                # 更新节点位置
                for value in current_move:
                    for i in range(1, 4): # 0:id, 1:x, 2:y, 3:z
                        node_position[int(value[0, 1]), i] = value[0, i+1]
                # 截取 (x,y,z) 坐标，用于下面节点位置更新
                node_id_position = node_position[:, [1, 2, 3]]

                # 所有节点更新位置，并发送hello至控制器
                # 所有节点广播hello包，向控制器报告位置
                for node in node_list:
                    node.update_node_position(node_id_position)
                    node.generate_hello_c(controller) # 控制器
                    #Gp.overhead[Gp.overhead_index] += 1

                # 控制器更新网络全局情况
                controller.predict_position() # 节点信息更新了，控制器也要根据hello列表的信息更新全局记录

                # 控制器获取区域和车的关系
                controller.analyze()

                # ------------------------1. 每次都初始化，将三个attribute值记录到Global_Par中------------------------
                # ------------------------2. 每次都初始化，将三个归一化后的attribute值记录到Global_Par中---------------
                # 用这一块时把下面全部注释
                # Gp中record列表记录了全部值，在一轮仿真完事后分析Gp中的列表的值
                #controller.init_routing_table()
                # Gp.biaoji = 1
                #-----------------------------------------------------------------------------------------------

                # 最开始初始化路由表，此后一个时间段内根据路由情况更新路由表
                if time == begin_time: #and x == 0:
                    controller.init_routing_table()

                # 控制器向所有节点发送其所属区域信息
                controller.send_area_info(node_list)

                # 所有节点广播hello包，向其他节点报告自身信息
                for node in node_list:
                    node.generate_hello_n(node_list) # 其他节点

                # 每个节点更新邻居表情况(包括邻居的基本信息以及所属区域信息)
                for node in node_list:
                    node.update_neighbor_list()

                #decrease所有源-目的对的strength值
                for current, dic in controller.routing_table.strength.items():
                    for target, streng in dic.items():
                        controller.routing_table.strength[current][target] -= 1 # Gp.total_delay[-1]
                        # 限制在>=0范围内
                        if controller.routing_table.strength[current][target] <= 0:
                            controller.routing_table.strength[current][target] = 0

                # 每秒发送多个数据包，选择数据发送节点和接收节点对:
                b = int(pkt_num/4)
                b1 = 0
                b2 = b
                b3 = 2*b
                b4 = 3*b
                for y in range(0, pkt_num):
                    if y == b1:
                        print("-----------------0-800----------------------")
                    if y == b2:
                        print("---------------800-1600-------------------------")
                    if y == b3:
                        print("----------------1600-2400---------------------------")
                    if y == b4:
                        print("-----------------2400-3200---------------------------")

                    if y==b1 or y==b2 or y==b3 or y==b4:
                        temp = Gp.success_time

                    source_id = -1
                    destination_id = -1
                    # 由远到近选择区域对，并在区域对中选择节点对
                    if y>=b1 and y<b2:
                        Gp.delay_hop_tag = 800
                        d_min = 0
                        d_max = 800
                    elif y>=b2 and y<b3:
                        Gp.delay_hop_tag = 1600
                        d_min = 800
                        d_max = 1600
                    elif y>=b3 and y<b4:
                        Gp.delay_hop_tag = 2400
                        d_min = 1600
                        d_max = 2400
                    else:
                        Gp.delay_hop_tag = 3200
                        d_min = 2400
                        d_max = 3200
                    # 随机选择区域对
                    while 1:
                        source_area = random.choice(list(Gp.it_pos))
                        candidate = []
                        for it, pos in Gp.it_pos.items():
                            x1 = Gp.it_pos[source_area][0]
                            y1 = Gp.it_pos[source_area][1]
                            x2 = pos[0]
                            y2 = pos[1]
                            d1 = getdis(x1, y1, x2, y2)
                            if d1>=d_min and d1<=d_max:
                                candidate.append(it)
                        # 在区域对中选择
                        while candidate:
                            destination_area = random.choice(candidate)
                            if controller.intra_vehicles_detail[source_area] and controller.intra_vehicles_detail[destination_area]:
                                source_id = random.choice(controller.intra_vehicles_detail[source_area])
                                destination_id = random.choice(controller.intra_vehicles_detail[destination_area])
                                break
                            candidate.remove(destination_area)
                        if source_id != -1 and destination_id != -1:
                            break
                    # 源节点发出路由请求（目的节点，控制器，包大小）
                    # 包大小为1024 bytes 总带宽为1930M byte ps = 1930 * 1024 * 1024 byte/s = 1930 * 2^20 bytes/s
                    # 1930*1024 = 1976320
                    # channel bandwidth = 6Mbps = 0.75 * 1024 * 1024 byte/s = 768 * 1024 byte/s
                    node_list[source_id].generate_request(destination_id, controller, 1024)

                    # 控制器处理路由请求
                    controller.resolve_request(node_list)

                    # 源节点发送数据包
                    node_list[source_id].forward_pkt(node_list, controller)

                    if y==b2-1:
                        Gp.success_0_800 += Gp.success_time - temp
                    elif y==b3-1:
                        Gp.success_800_1600 += Gp.success_time - temp
                    elif y==b4-1:
                        Gp.success_1600_2400 += Gp.success_time - temp
                    elif y==pkt_num-1:
                        Gp.success_2400_3200 += Gp.success_time - temp
                    else:
                        continue


                # 找出F为0的源-目的区域，随机选出节点，发送虚拟数据包
                # 在选区时,以random方式
                test_ = 0
                Gp.test_success.append(0)
                update_pair = []
                for current, dic in controller.routing_table.strength.items():
                    for target, strength in dic.items():
                        # 同区和邻区不维护
                        if current == target or current in Gp.adjacents_comb[target]:
                            continue
                        if strength == 0: # 如果为0，就派出测试数据包
                            #print("test from x->y:", current, target)
                            update_pair.append([current, target])
                if len(update_pair)>1000:
                    act = random.sample(update_pair, 1000)
                else:
                    act = update_pair
                for pair in act:
                    current = pair[0]
                    target = pair[1]
                    # 控制器在两个区域中分别随机指定车辆，并要求源车辆向目的车辆发送数据包
                    source_test_id = controller.send_test_request(node_list, current, target)
                    # 源节点发送数据包
                    if source_test_id == -1:
                        #print("can not find vehicles in test source/target areas")
                        continue
                    elif source_test_id == -2:
                        #print("can not find the candidate at the first step")
                        continue
                    else:
                        test_ += 1 # 测试包数量+1
                        Gp.overhead[Gp.overhead_index] += 1
                        node_list[source_test_id].forward_test_pkt(node_list, controller)
                # 记录测试包数量
                Gp.test_num.append(test_)  # [num1, num2,...]

                # 控制器处理汇报信息，更新路由表
                controller.resolve_report()

                # 清空
                #controller.intra_vehicles_detail = {i: [] for i in Gp.intersection.keys()}

            # 一轮仿真结束，获取结束时间
            end_time = t.time()

            # 测试包数量 {x:[],...}
            Gp.total_test_num[x] = Gp.test_num
            # 数据包时延
            Gp.total_pkt_delay[x] = Gp.pkt_delay
            Gp.total_pkt_delay_800[x] = Gp.pkt_delay_800
            Gp.total_pkt_delay_1600[x] = Gp.pkt_delay_1600
            Gp.total_pkt_delay_2400[x] = Gp.pkt_delay_2400
            Gp.total_pkt_delay_3200[x] = Gp.pkt_delay_3200
            # 数据包跳数
            Gp.total_hop_list[x] = Gp.hop_list
            Gp.total_hop_list_800[x] = Gp.hop_list_800
            Gp.total_hop_list_1600[x] = Gp.hop_list_1600
            Gp.total_hop_list_2400[x] = Gp.hop_list_2400
            Gp.total_hop_list_3200[x] = Gp.hop_list_3200

            # 数据包
            print("success num:", Gp.success_time)
            print("loss num:", Gp.fail_time)
            print("loss in area selection:", Gp.loop_fail_time)
            print("delay from generation to delivery or loss: ")
            print("hop: ")
            # 测试数据包
            print("number of test packets: ", Gp.test_num)
            print("number of successful test packets: ", Gp.test_success)
            print("test loss in area selection:", Gp.test_loop_fail_time)

            # 记录单次仿真情况到列表
            Gp.success_time_list.append(Gp.success_time)
            Gp.success_0_800_list.append(Gp.success_0_800)
            Gp.success_800_1600_list.append(Gp.success_800_1600)
            Gp.success_1600_2400_list.append(Gp.success_1600_2400)
            Gp.success_2400_3200_list.append(Gp.success_2400_3200)
            Gp.fail_time_list.append(Gp.fail_time)
            Gp.loop_file_time_list.append(Gp.loop_fail_time)
            Gp.test_loop_fail_time_list.append(Gp.test_loop_fail_time)
            # 清空临时存储
            Gp.test_num = []
            Gp.test_success = []
            Gp.success_time = 0
            Gp.success_0_800 = 0
            Gp.success_800_1600 = 0
            Gp.success_1600_2400 = 0
            Gp.success_2400_3200 = 0
            Gp.fail_time = 0
            Gp.loop_fail_time = 0
            Gp.test_loop_fail_time = 0
            Gp.pkt_delay = []
            Gp.pkt_delay_800 = []
            Gp.pkt_delay_1600 = []
            Gp.pkt_delay_2400 = []
            Gp.pkt_delay_3200 = []
            Gp.hop_list = []
            Gp.hop_list_800 = []
            Gp.hop_list_1600 = []
            Gp.hop_list_2400 = []
            Gp.hop_list_3200 = []

        # 在一个场景下进行多次仿真
        # 仿真结束后计算总值
        success = np.array(Gp.success_time_list)
        fail = np.array(Gp.fail_time_list)
        loop = np.array(Gp.loop_file_time_list)
        succ = np.sum(success) # 总成功次数
        total = np.sum(success) + np.sum(fail) + np.sum(loop) # 总数据包数
        ratio = round(succ / total,3) # 到达率
        success_800 = np.array(Gp.success_0_800_list)
        success_1600 = np.array(Gp.success_800_1600_list)
        success_2400 = np.array(Gp.success_1600_2400_list)
        success_3200 = np.array(Gp.success_2400_3200_list)
        succ_800 = np.sum(success_800)
        succ_1600 = np.sum(success_1600)
        succ_2400 = np.sum(success_2400)
        succ_3200 = np.sum(success_3200)
        ratio_800 = round(succ_800 / (total / 4),3)
        ratio_1600 = round(succ_1600 / (total / 4),3)
        ratio_2400 = round(succ_2400 / (total / 4),3)
        ratio_3200 = round(succ_3200 / (total / 4),3)
        print(Gp.success_time_list, Gp.success_0_800_list, Gp.success_800_1600_list, Gp.success_1600_2400_list,
              Gp.success_2400_3200_list)
        print(total)
        print(ratio_800, ratio_1600, ratio_2400, ratio_3200)
        average_hop = [] # 每次仿真的平均跳数
        average_hop_800 = []
        average_hop_1600 = []
        average_hop_2400 = []
        average_hop_3200 = []
        average_delay = [] # 每次仿真的平均跳数
        average_delay_800 = []
        average_delay_1600 = []
        average_delay_2400 = []
        average_delay_3200 = []

        # 补全hop
        for x_, hop_list in Gp.total_hop_list.items():
            max_hop = max(hop_list)
            for i_ in range(0,total-len(hop_list)):
                Gp.total_hop_list[x_].append(max_hop)
        for x_, hop_list in Gp.total_hop_list_800.items():
            max_hop = max(hop_list)
            for i_ in range(0,int(total/4)-len(hop_list)):
                Gp.total_hop_list_800[x_].append(max_hop)
        for x_, hop_list in Gp.total_hop_list_1600.items():
            max_hop = max(hop_list)
            for i_ in range(0,int(total/4)-len(hop_list)):
                Gp.total_hop_list_1600[x_].append(max_hop)
        for x_, hop_list in Gp.total_hop_list_2400.items():
            max_hop = max(hop_list)
            for i_ in range(0,int(total/4)-len(hop_list)):
                Gp.total_hop_list_2400[x_].append(max_hop)
        for x_, hop_list in Gp.total_hop_list_3200.items():
            max_hop = max(hop_list)
            for i_ in range(0,int(total/4)-len(hop_list)):
                Gp.total_hop_list_3200[x_].append(max_hop)
        # 计算hop
        for x_, hop_list in Gp.total_hop_list.items():
            hops = np.array(hop_list)
            average_hop.append(np.mean(hops))
        for x_, hop_list in Gp.total_hop_list_800.items():
            hops = np.array(hop_list)
            average_hop_800.append(np.mean(hops))
        for x_, hop_list in Gp.total_hop_list_1600.items():
            hops = np.array(hop_list)
            average_hop_1600.append(np.mean(hops))
        for x_, hop_list in Gp.total_hop_list_2400.items():
            hops = np.array(hop_list)
            average_hop_2400.append(np.mean(hops))
        for x_, hop_list in Gp.total_hop_list_3200.items():
            hops = np.array(hop_list)
            average_hop_3200.append(np.mean(hops))

        # 补全delay
        for x_, delay_list in Gp.total_pkt_delay.items():
            max_delay = max(delay_list)
            for i_ in range(0, int(total/4)-len(delay_list)):
                Gp.total_pkt_delay[x_].append(max_delay)
        for x_, delay_list in Gp.total_pkt_delay_800.items():
            max_delay = max(delay_list)
            for i_ in range(0, int(total/4)-len(delay_list)):
                Gp.total_pkt_delay_800[x_].append(max_delay)
        for x_, delay_list in Gp.total_pkt_delay_1600.items():
            max_delay = max(delay_list)
            for i_ in range(0, int(total/4)-len(delay_list)):
                Gp.total_pkt_delay_1600[x_].append(max_delay)
        for x_, delay_list in Gp.total_pkt_delay_2400.items():
            max_delay = max(delay_list)
            for i_ in range(0, int(total/4)-len(delay_list)):
                Gp.total_pkt_delay_2400[x_].append(max_delay)
        for x_, delay_list in Gp.total_pkt_delay_3200.items():
            max_delay = max(delay_list)
            for i_ in range(0, int(total/4)-len(delay_list)):
                Gp.total_pkt_delay_3200[x_].append(max_delay)
        # 计算delay
        for x_, delay_list in Gp.total_pkt_delay.items():
            delays = np.array(delay_list)
            average_delay.append(np.mean(delays))
        for x_, delay_list in Gp.total_pkt_delay_800.items():
            delays = np.array(delay_list)
            average_delay_800.append(np.mean(delays))
        for x_, delay_list in Gp.total_pkt_delay_1600.items():
            delays = np.array(delay_list)
            average_delay_1600.append(np.mean(delays))
        for x_, delay_list in Gp.total_pkt_delay_2400.items():
            delays = np.array(delay_list)
            average_delay_2400.append(np.mean(delays))
        for x_, delay_list in Gp.total_pkt_delay_3200.items():
            delays = np.array(delay_list)
            average_delay_3200.append(np.mean(delays))

        for i in range(0,len(Gp.overhead)):
            Gp.overhead[i] = Gp.overhead[i]/3

        # 切换车辆文件，将本次记录写入文件中
        with open('overhead_result.txt', 'a+') as f:
            f.write(movement_file + '\n')
            # f.write("success nums: " +  str(Gp.success_time_list) + '\n')
            # f.write("loss nums: " +  str(Gp.fail_time_list) + '\n')
            # f.write("loss in area selection nums: " +  str(Gp.loop_file_time_list) + '\n')
            # f.write("total delivery time: " + str(succ) + '\n')
            # f.write("total packets time: " + str(total) + '\n')
            # f.write("delivery rate: " + str(ratio) + '\n')
            # f.write("delivery rate in 0-800: " + str(ratio_800) + '\n')
            # f.write("delivery rate in 800-1600: " + str(ratio_1600) + '\n')
            # f.write("delivery rate in 1600-2400: " + str(ratio_2400) + '\n')
            # f.write("delivery rate in 2400-3200: " + str(ratio_3200) + '\n')
            # f.write("average hops: " + str(np.mean(np.array(average_hop))) + '\n')
            # f.write("average hops in 0-800: " + str(np.mean(np.array(average_hop_800))) + '\n')
            # f.write("average hops in 800-1600: " + str(np.mean(np.array(average_hop_1600))) + '\n')
            # f.write("average hops in 1600-2400: " + str(np.mean(np.array(average_hop_2400))) + '\n')
            # f.write("average hops in 2400-3200: " + str(np.mean(np.array(average_hop_3200))) + '\n')
            # f.write("average delay: " + str(np.mean(np.array(average_delay))) + '\n')
            # f.write("average delay in 0-800: " + str(np.mean(np.array(average_delay_800))) + '\n')
            # f.write("average delay in 800-1600: " + str(np.mean(np.array(average_delay_1600))) + '\n')
            # f.write("average delay in 1600-2400: " + str(np.mean(np.array(average_delay_2400))) + '\n')
            # f.write("average delay in 2400-3200: " + str(np.mean(np.array(average_delay_3200))) + '\n')
            f.write("average communication overhead: " + str(Gp.overhead) + '\n')

        f = xlwt.Workbook()
        sheet1 = f.add_sheet(u'sheet1', cell_overwrite_ok=True)  # 创建sheet
        for j in range(len(Gp.overhead)):
            sheet1.write(j, u, Gp.overhead[j])


            # f.write("average hops: " + str(average_hop) + '\n')
            # f.write("average hops in 0-800: " + str(average_hop_800) + '\n')
            # f.write("average hops in 800-1600: " + str(average_hop_1600) + '\n')
            # f.write("average hops in 1600-2400: " + str(average_hop_2400) + '\n')
            # f.write("average hops in 2400-3200: " + str(average_hop_3200) + '\n')
            # f.write("average delay: " + str(average_delay) + '\n')
            # f.write("average delay in 0-800: " + str(average_delay_800) + '\n')
            # f.write("average delay in 800-1600: " + str(average_delay_1600) + '\n')
            # f.write("average delay in 1600-2400: " + str(average_delay_2400) + '\n')
            # f.write("average delay in 2400-3200: " + str(average_delay_3200) + '\n')
            # 写入数据包跳数
            # f.write('packet hop: ' + '\n')
            # for x, hops in Gp.total_hop_list.items():
            #     f.write(str(hops) + '\n')
            # 写入数据包时延
            # f.write('packet delay: ' + '\n')
            # for x, delays in Gp.total_pkt_delay.items():
            #     f.write(str(delays) + '\n')
            # 写入测试数据包数量
            # f.write('test packets number: ' + '\n')
            # for x, test in Gp.total_test_num.items():
            #     f.write(str(test) + '\n')

        # 清空存储
        Gp.total_test_num = {}
        Gp.total_pkt_delay = {}
        Gp.total_pkt_delay_800 = {}
        Gp.total_pkt_delay_1600 = {}
        Gp.total_pkt_delay_2400 = {}
        Gp.total_pkt_delay_3200 = {}
        Gp.total_hop_list = {}
        Gp.total_hop_list_800 = {}
        Gp.total_hop_list_1600 = {}
        Gp.total_hop_list_2400 = {}
        Gp.total_hop_list_3200 = {}
        Gp.success_time_list = []
        Gp.success_0_800_list = []
        Gp.success_800_1600_list = []
        Gp.success_1600_2400_list = []
        Gp.success_2400_3200_list = []
        Gp.fail_time_list = []
        Gp.loop_file_time_list = []
        Gp.test_loop_fail_time_list = []
        Gp.overhead = []

    f.save("x_test_2000.xls")  # 保存文件

        # # -----------------以下仅用于统计归一化时的参数------------------
        # # 在初始化时获取每个区域的分布情况，两区域之间连通性，有效距离
        # Gp.distribution_record = []
        # Gp.connectivity_record = []
        # Gp.distance_record = []
        # 分布：
        #   miu：Gp.distribution_avg   所有数值的平均值
        #   sigma：Gp.distribution_var   所有数值的方差
        # 连通：
        #   Gp.connectivity_min  所有数值的最小值
        #   Gp.connectivity_max  所有数值的最小值
        # 距离：
        #   Gp.distance_min  所有数值的最小值
        #   Gp.distance_max  所有数值的最大值
        # Gp.connectivity_record.sort()
        # connectivity = np.array(Gp.connectivity_record)
        # connectivity_min = min(connectivity)
        # connectivity_max = max(connectivity)
        # connectivity_var = np.std(connectivity)
        # print("connectivity min,  max,  var: ", connectivity_min, connectivity_max, connectivity_var)
        #
        # plt.title("connectivity")
        # x1 = list(range(0, len(Gp.connectivity_record)))
        # y1 = Gp.connectivity_record
        # for i in range(len(x1)):
        #     plt.scatter(x1[i], y1[i], color='k', alpha=0.3)
        # plt.show()
        #
        # Gp.distance_record.sort()
        # distance = np.array(Gp.distance_record)
        # distance_min = min(Gp.distance_record)
        # distance_max = max(Gp.distance_record)
        # distance_var = np.std(distance)
        # print("valid distance min, max, vat: ", distance_min, distance_max, distance_var)
        #
        # plt.figure()
        # plt.title("valid distance")
        # x3 = list(range(0, len(Gp.distance_record)))
        # y3 = Gp.distance_record
        # for i in range(0,len(x3),100):
        #     plt.scatter(x3[i], y3[i], color='k', alpha=0.3)
        # plt.show()
        #
        # Gp.distribution_record.sort()
        # distribution = np.array(Gp.distribution_record)
        # distribution_min = min(distribution)
        # distribution_max = max(distribution)
        # distribution_var = np.std(distribution)
        # print("distribution min, max, var: ", distribution_min, distribution_max, distribution_var)
        #
        # plt.figure()
        # plt.title("distribution")
        # x2 = list(range(0, len(Gp.distribution_record)))
        # y2 = Gp.distribution_record
        # for i in range(len(x2)):
        #     plt.scatter(x2[i], y2[i], color='k', alpha=0.3)
        # plt.show()

        # #------------------------写入文件-------------------------------------
        # with open('a_record.txt', 'a+') as f:
        #     f.write(movement_file + '\n')
        #     f.write('connectivity_min '+ str(connectivity_min) + '\n')
        #     f.write('connectivity_max '+ str(connectivity_max) + '\n')
        #     f.write('connectivity_var ' + str(connectivity_var) + '\n')
        #     f.write('distance_min '+ str(distance_min) + '\n')
        #     f.write('distance_max '+ str(distance_max) + '\n')
        #     f.write('distance_var ' + str(distance_var) + '\n')
        #     f.write('distribution_min '+ str(distribution_min) + '\n')
        #     f.write('distribution_var '+ str(distribution_var) + '\n')
        #     f.write('distribution_max '+ str(distribution_max) + '\n')
        #     f.write('\n')
        # with open('attributes_record.txt', 'w') as f:
        #     f.writelines(str(Gp.distribution_record))
        #     f.writelines(str(Gp.connectivity_record))
        #     f.writelines(str(Gp.distance_record))
        #--------------------------------------------------------------------


        # -----------------以下仅用于三个attribute的模糊集合划分------------------
        ## mixed distribution: poor: a, b, medium, a, b=c, d, good: a, b
        ## one-way connectivity: low: a, b, middle: a, b=c, d, high: a, b
        ## valid distance: close: a, b, medium: a, b=c, d, far: a, b
        #
        # Gp.normalized_distribution_record.sort()
        # print(Gp.normalized_distribution_record)
        # print(len(Gp.normalized_distribution_record))
        # nor_distribution_min = Gp.normalized_distribution_record[0]
        # nor_distribution_max = Gp.normalized_distribution_record[-1]
        # nor_distribution_cen = Gp.normalized_distribution_record[math.ceil(len(Gp.normalized_distribution_record)/2)]
        # print("normalized distribution min, cen, max:", nor_distribution_min, nor_distribution_cen, nor_distribution_max)
        # Gp.normalized_connectivity_record.sort()
        # nor_connectivity_min = Gp.normalized_connectivity_record[0]
        # nor_connectivity_max = Gp.normalized_connectivity_record[-1]
        # nor_connectivity_cen = Gp.normalized_connectivity_record[math.ceil(len(Gp.normalized_connectivity_record)/2)]
        # print(Gp.normalized_connectivity_record)
        # print(len(Gp.normalized_connectivity_record))
        # print("normalized connectivity min, cen, max:", nor_connectivity_min, nor_connectivity_cen, nor_connectivity_max)
        # Gp.normalized_distance_record.sort()
        # nor_distance_min = Gp.normalized_distance_record[0]
        # nor_distance_max = Gp.normalized_distance_record[-1]
        # nor_distance_cen = Gp.normalized_distance_record[math.ceil(len(Gp.normalized_distance_record)/2)]
        # print(Gp.normalized_distance_record)
        # print(len(Gp.normalized_distance_record))
        # print("normalized distance min, cen, max:", nor_distance_min, nor_distance_cen, nor_distance_max)
        # # ----------------------------写入文件---------------------------------
        # with open('a_record_nor.txt', 'a+') as f:
        #     f.write(movement_file + '\n')
        #     f.write('nor_connectivity_min'+ str(nor_connectivity_min) + '\n')
        #     f.write('nor_connectivity_cen' + str(nor_connectivity_cen) + '\n')
        #     f.write('nor_connectivity_max'+ str(nor_connectivity_max) + '\n')
        #     f.write('nor_distance_min'+ str(nor_distance_min) + '\n')
        #     f.write('nor_distance_cen' + str(nor_distance_cen) + '\n')
        #     f.write('nor_distance_max'+ str(nor_distance_max) + '\n')
        #     f.write('nor_distribution_min'+ str(nor_distribution_min) + '\n')
        #     f.write('nor_distribution_cen' + str(nor_distribution_cen) + '\n')
        #     f.write('nor_distribution_max'+ str(nor_distribution_max) + '\n')
        #     f.write('\n')
        # # with open('nor_distribution.txt', 'w') as f:
        # #     f.writelines(str(Gp.normalized_distribution_record))
        # # with open('nor_connectivity.txt', 'w') as f:
        # #     f.writelines(str(Gp.normalized_connectivity_record))
        # # with open('nor_distance.txt', 'w') as f:
        # #     f.writelines(str(Gp.normalized_distance_record))
        #
        # x1 = list(range(0,len(Gp.normalized_distribution_record)))
        # y1 = Gp.normalized_distribution_record
        # for i in range(len(x1)):
        #     plt.scatter(x1[i], y1[i], color='k', alpha=0.3)
        # plt.show()
        # plt.figure()
        #
        # x2 = list(range(0, len(Gp.normalized_connectivity_record)))
        # y2 = Gp.normalized_connectivity_record
        # for i in range(len(x2)):
        #     plt.scatter(x2[i], y2[i], color='k', alpha=0.3)
        # plt.show()
        # plt.figure()
        # #
        # x3 = list(range(0, len(Gp.normalized_distance_record)))
        # y3 = Gp.normalized_distance_record
        # for i in range(0,len(x3),100):
        #     plt.scatter(x3[i], y3[i], color='k', alpha=0.3)
        # plt.show()
        #-----------------------------------------------------------------------













        # # #-----------------------------------------------------------------------------------------------------------------------
        # x = []
        # y = []
        # txt = []
        # for it, pos in Gp.it_pos.items():
        #     txt.append(it)
        #     x.append(pos[0])
        #     y.append(pos[1])
        # plt.scatter(x, y)
        # for i in range(len(x)):
        #     plt.annotate(txt[i], xy=(x[i], y[i]), xytext=(x[i] + 0.5, y[i] + 0.5))  # 这里xy是需要标记的坐标，xytext是对应的标签坐标
        # controller.intersectionn()
        # #-----------------------------------------------------------------------------------------------------------------------
        # x = []
        # y = []
        # nx = []
        # ny = []
        # txt = []
        # for it, pos in Gp.intersection.items():
        #     f = 0
        #     for oo in Gp.intersections_combination:
        #         if it in oo:
        #             f = 1
        #     if f == 1:
        #         nx.append(pos[0])
        #         ny.append(pos[1])
        #         continue
        #     x.append(pos[0])
        #     y.append(pos[1])
        # plt.scatter(nx, ny, color='r')
        # plt.scatter(x, y)
        # #plt.show()
        # #plt.figure()
        # street_x = []
        # street_y = []
        # street_x, street_y= trail_analysis.map(street_x, street_y)
        # for i in range(len(street_x)):
        #     plt.plot(street_x[i], street_y[i], color='k', alpha=0.3)
        # plt.show()
        # controller.intersections()
        # # #---------------------------------------------------------------------------------------------------------------------------


## 画车辆运动情况
# plt.clf()
# x = []
# y = []
# for node in node_list:
#     x.append(node.position[0])
#     y.append(node.position[1])
# plt.scatter(x, y, color='r',alpha=1)
# plt.pause(0.1)
# continue




            #     effi += end_time-start_time # 仿真时间
            #     delay += Gp.sum  # 时延
            #     Gp.sum = 0
            #     std2 += np.std(Gp.record, ddof=1) # 抖动 np.std计算矩阵的标准差
            #
            #     Gp.record.clear()
            #     com_node_list.clear()
            #
            # print('\ncalculation time:\n')
            # print(effi)
            # print('\ndelay:\n')
            # print(delay)
            # print('\njitter:\n')
            # print(std2)
            # print('\ndelivery ratio:\n')
            # print(Gp.fail_time)



# 统计不属于任何区域的车
# liss = 0
# plt.clf()
# x = []
# y = []
# for node in node_list:
#     if node.area:
#         liss += 1
#         x.append(node.position[0])
#         y.append(node.position[1])
# plt.scatter(x, y, color='r',alpha=1)
# plt.pause(0.1)
# valid_nodes_num.append(liss)
# print(liss)
# print(valid_nodes_num)
# continue

# 根据节点总数和通信节点比例，获得n对通信节点：[[发id,收id],[发id,收id],[发id,收id],....]
# com_node_list.extend(Init.get_communication_node(node_num-1))
# com_node_list.extend(Init.get_communication_node(node_num-1, sim_time-begin_time))
# print("communication nodes list:", com_node_list)
# print("number of vehicles:", node_num)
# print("number of communication node list:", len(com_node_list))
# # 获取数据发送节点和接收节点
# source_id = com_node_list[time-begin_time][0]
# destination_id = com_node_list[time-begin_time][1]
# while 1:
#     if node_list[source_id].area and node_list[destination_id].area:
#         break
#     else:
#         source_id = random.randint(0, len(node_list)-1)
#         destination_id = random.randint(0, len(node_list)-1)

#
# total_test = 0
# for u in Gp.test_num:
#     total_test += u
# print("total number of test packets", total_test)