
import numpy as np
import re 
import matplotlib.pyplot as plt
import Init
import Global_Par as gp


def get_position(mobile_file_path):
    x_max = 0
    y_max = 0
    z_max = 0
    with open(mobile_file_path, 'r') as f:
        movement_list = []
        init_position_list = []
        item_list = []
        key = 0
        for line in f:
            line_list = re.split('[\s]', line)
            if line_list[5] != 'set':
                item_list.append(int(float(line_list[2])))
                item_list.append(float(line_list[3][8:-1]))
                if float(line_list[5]) > x_max:
                    x_max = float(line_list[5])
                if float(line_list[6]) > y_max:
                    y_max = float(line_list[6])
                if float(line_list[7][0:-1]) > z_max:
                    z_max = float(line_list[7][0:-1])
                item_list.append(float(line_list[5]))
                item_list.append(float(line_list[6]))
                item_list.append(float(line_list[7][0:-1]))
                movement_list.append(item_list)
                item_list = []
            else:
                key = key + 1
                if key % 3 == 1:
                    item_list.append(int(line_list[2][7:-1]))
                if key % 3 != 0:
                    item_list.append(float(line_list[7]))
                if key % 3 == 0:
                    item_list.append(float(line_list[7]))
                    init_position_list.append(item_list)
                    item_list = []
        movement_matrix = np.mat(movement_list)
        init_position_matrix = np.mat(init_position_list)
        return movement_matrix, init_position_matrix

def update_node_position(movement_matrix, node_position, start_t, update_period, animation, nodelist, com_nodelist, controller):

    print('开始时间:', start_t)
    active_route = []
    current_move = movement_matrix[np.nonzero(movement_matrix[:, 0].A == start_t)[0], :]
    print(current_move)
    for value in current_move:
        for i in range(2, 4):
            node_position[int(value[0, 1]), i+2] = value[0, i]
    speed_x = node_position[:, 4] - node_position[:, 2]
    speed_y = node_position[:, 5] - node_position[:, 3]
    for i in range(0, int(1.0/gp.update_period)):
        node_position[:, 2] = node_position[:, 2] + speed_x * gp.update_period
        node_position[:, 3] = node_position[:, 3] + speed_y * gp.update_period
        node_id_position = node_position[:, [1, 2, 3]]
        if nodelist == [] or com_nodelist == []:
            nodelist.extend(Init.init_node(node_id_position, controller))
            com_nodelist.extend(Init.get_communication_node(node_id_position.shape[0]))
            print('所有通信节点:', com_nodelist)
        if animation:
            plt.clf()
            plt.plot(node_position[:, 2], node_position[:, 3], '.m')
            plt.pause(0.01)
