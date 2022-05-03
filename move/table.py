import numpy as np
import pandas as pd
import math
import Global_Par as Gp

class Routing_Table:
    def __init__(self, intersection):
        self.table = {current: {target: {neighbor: 0 for neighbor in Gp.adjacents_comb[current]} for target in Gp.it_pos} for current in Gp.it_pos}  # 路由表
        #self.table = self.table_config()
        # 路由表
        self.strength = {current: {target: 0 for target in intersection} for current in intersection} # 从current到target的路径strength
        self.distribution = {current: 0 for current in intersection}
        self.connectivity = {current: {adjacent: 0 for adjacent in Gp.adjacents_comb[current]} for current in intersection}
        self.final_distribution = {current: {adjacent: 0 for adjacent in Gp.adjacents_comb[current]} for current in intersection}
        self.final_connectivity = {current: {adjacent: 0 for adjacent in Gp.adjacents_comb[current]} for current in intersection}

    # # 路由表矩阵, 字典改dataframe
    # 在选择元素时，先定位列（target），再定位第一维行（current），最后第二维行（adjacent）
    def table_config(self):
        index1 = []
        index2 = []
        column_ = []
        column_len = len(Gp.it_pos)
        row_len = 0
        for it, neibs in Gp.adjacents_comb.items():
            column_.append(it)
            row_len += len(neibs)
            index2.extend(neibs)
            for i in range(0, len(neibs)):
                index1.append(it)
        index_ = [index1, index2]
        # print(row_len)
        # print(column_len)
        D = pd.DataFrame(np.zeros((row_len, column_len)), index=index_, columns=column_)
        print(D)
        return D


    def get_traffic_info(self, current, adjacent, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length):
        half_num = intra_vehicles_number[adjacent]  # [num1, num2,...]
        half_length = intra_path_length[adjacent]  # {len1, len2,...}
        part_num = inter_vehicles_number[current][adjacent]  # [veh_num1, veh_num2,...]
        part_length = inter_part_length[current][adjacent]  # float
        return half_num, half_length, part_num, part_length

    def initial(self, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length):

        for current in Gp.it_pos:
            half_num_1 = intra_vehicles_number[current]
            half_length_1 = intra_path_length[current]
            distribution_crisp = Exact.distribution(half_num_1, half_length_1)
            self.distribution[current] = distribution_crisp
            for ne in Gp.adjacents_comb[current]:
                part_num_1 = inter_vehicles_number[current][ne]
                part_length_1 = inter_part_length[current][ne]
                connectivity_crisp = Exact.connectivity(part_num_1, part_length_1)
                self.connectivity[current][ne] = connectivity_crisp


        for current in Gp.it_pos:
            conn_sum = 0
            distr_sum = 0
            ssd = []
            for neb in Gp.adjacents_comb[current]:
                conn_sum += self.connectivity[current][neb]
                distr_sum += self.distribution[neb]
                ssd.append(self.distribution[neb])
            conn_avg = conn_sum / len(Gp.adjacents_comb[current])
            distr_avg = distr_sum / len(Gp.adjacents_comb[current])
            distr_max = max(ssd)
            for neb in Gp.adjacents_comb[current]:
                if self.connectivity[current][neb] != 0:
                    final_conn = math.log(1 + self.connectivity[current][neb] / conn_avg)
                else:
                    final_conn = 0
                final_distr = self.distribution[neb] / distr_avg - self.distribution[neb]/ distr_max
                if final_conn > 1:
                    final_conn = 1
                if final_distr > 1:
                    final_distr = 1
                Gp.distribution_record.append(final_distr)
                Gp.connectivity_record.append(final_conn)
                self.final_connectivity[current][neb] = final_conn
                self.final_distribution[current][neb] = final_distr
        for current in Gp.it_pos:
            for target in Gp.it_pos:
                if current == target:
                    weight = 10
                    self.table[current][target][current] = weight
                elif current in Gp.adjacents_comb[target]:
                    weight = 10
                    self.table[current][target][target] = weight
                else:
                    for neib in Gp.adjacents_comb[current]:
                        valid_distance_crisp = Exact.valid_distance(current,neib,target)
                        Gp.distance_record.append(valid_distance_crisp)
                        distribution_crisp = self.final_distribution[current][neib]
                        connectivity_crisp = self.final_connectivity[current][neib]
                        weight = FuzR.fuzzy_routing(distribution_crisp, connectivity_crisp, valid_distance_crisp)
                        self.table[current][target][neib] = weight
        return

    def update_strength(self, current_area, target_area):
        max = 0
        for neb1 in Gp.adjacents_comb[current_area]:
            for neb2 in Gp.adjacents_comb[target_area]:
                if self.strength[neb1][neb2] > max:
                    max = self.strength[neb1][neb2]
        if max > Gp.constant_strength:
            self.strength[current_area][target_area] += max
        else:
            self.strength[current_area][target_area] += Gp.constant_strength
        return

    def get_positive_reward(self, current, target, adjacent, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length):
        connectivity, distribution, distance = Exact.crisp(current, adjacent, target, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length)
        reward = Gp.positive_a * distribution + Gp.positive_b * connectivity + Gp.positive_c * distance
        return reward


    def positive_update(self, path, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length):
        if len(path) == 1 or len(path) == 2:
            return
        for current in path[::-1]:
            if current == path[-1] or current == path[-2]:
                continue
            next = path[path.index(current)+1]
            for child in path[path.index(current)+1: len(path)]:
                for target in Gp.adjacents_comb[child]:
                    if target == path[path.index(child)-1]:
                        continue
                    if target == current:
                        continue
                    if target in Gp.adjacents_comb[current]:
                        continue
                    if self.strength[current][target] != 0:
                        continue
                    alpha = path.index(child) + 1 - path.index(current)
                    alpha = min(0.9, max(0.3, 1 / alpha))
                    reward = self.get_positive_reward(current, target, next, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length)
                    MAX = max(self.table[next][target].values())
                    self.table[current][target][next] += alpha * (reward + Gp.q_gamma * (MAX - self.table[current][target][next]))
                    self.update_strength(current, target)


            for neib in Gp.adjacents_comb[current]:
                if neib == path[path.index(current)+1]:
                    continue
                if path.index(current) != 0:
                    if neib == path[path.index(current)-1]:
                        continue
                for child in path[path.index(current)+1: len(path)-1]:
                    for target in Gp.adjacents_comb[child]:
                        if target == path[path.index(child)-1]:
                            continue
                        if target == neib or target == current:
                            continue
                        if target in Gp.adjacents_comb[neib]:
                            continue
                        if self.strength[current][target] != 0:
                            continue
                        alpha = path.index(child) + 1 - path.index(current) + 1
                        alpha = min(0.9, max(0.3, 1/alpha))
                        reward = self.get_positive_reward(neib, target, current, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length)
                        MAX = max(self.table[current][target].values())
                        self.table[neib][target][current] += alpha * (reward + Gp.q_gamma * (MAX - self.table[neib][target][current]))
                        self.update_strength(neib,target)
        return

    def get_negative_reward11(self, loss_area, neib_area, target_area, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length):
        connectivity, distribution, distance = Exact.crisp(neib_area, loss_area, target_area, intra_vehicles_number,
                                                           intra_path_length, inter_vehicles_number, inter_part_length)
        reward = Gp.negative_a * (1-distribution) - (1 - Gp.negative_b) * distance
        return reward
    def get_negative_reward12(self, loss_area, next_area, target_area, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length):
        connectivity, distribution, distance = Exact.crisp(loss_area, next_area, target_area, intra_vehicles_number,
                                                           intra_path_length, inter_vehicles_number, inter_part_length)
        reward = Gp.negative_b * (1-connectivity) - (1 - Gp.negative_b) * distance
        return reward


    def negative_update1(self, path, loss_area, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length):
        flag = 0
        target_area = path[-1]
        if loss_area == path[-1]:
            return
        elif loss_area == path[-2]:
            flag = 1
            next_area = path[path.index(loss_area) + 1]
        else:
            next_area = path[path.index(loss_area) + 1]

        failure_neibs = Gp.adjacents_comb[loss_area]
        for neib in failure_neibs:
            if neib == next_area:
                continue
            reward = self.get_negative_reward11(loss_area, neib, target_area, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length)
            a = self.table[neib][target_area][loss_area]
            self.table[neib][target_area][loss_area] += Gp.q_alpha * (-reward)
            if self.table[neib][target_area][loss_area] < 0:
                self.table[neib][target_area][loss_area] = 0
            self.update_strength(neib, target_area)
        if flag == 1:
            return
        reward = self.get_negative_reward12(loss_area, next_area, target_area, intra_vehicles_number, intra_path_length, inter_vehicles_number, inter_part_length)
        a = self.table[loss_area][target_area][next_area]
        self.table[loss_area][target_area][next_area] += Gp.q_alpha * (-reward)
        if self.table[loss_area][target_area][next_area] < 0:
            self.table[loss_area][target_area][next_area] = 0
        self.update_strength(loss_area, target_area)
        return
    def get_negative_reward2(self, type):
        return
    def negative_update2(self, path, loss_area):
        target_area = path[-1]
        failure_neibs = Gp.adjacents[loss_area]
        return



