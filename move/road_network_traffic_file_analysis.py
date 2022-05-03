import numpy as np
import matplotlib.pyplot as plt
import re
import math
import Global_Par as Gp
import copy


def nldis(pointX,pointY,lineX1,lineY1,lineX2,lineY2):
    a=lineY2-lineY1
    b=lineX1-lineX2
    c=lineX2*lineY1-lineX1*lineY2
    dis=(math.fabs(a*pointX+b*pointY+c))/(math.pow(a*a+b*b,0.5))
    return dis


def nndis(ax, ay, bx, by):
    temp_x = ax - bx
    temp_y = ay - by
    temp_x = temp_x * temp_x
    temp_y = temp_y * temp_y
    result = math.sqrt(temp_x+temp_y)
    return result


def angle(x0, y0, x1, y1, x2, y2):
    cos = ((x1-x0)*(x2-x0)+(y1-y0)*(y2-y0))/(math.sqrt(pow(x1-x0, 2)+pow(y1-y0, 2)) * math.sqrt(pow(x2-x0, 2)+pow(y2-y0, 2)))
    theta = math.acos(cos) / math.pi
    return theta


def junction():
    junction_file = "tiexi_intersection.xml"
    junctions_coordinate = {} # id:[x,y]
    junctions_connect = {} #id:[id,id,...,id]
    with open(junction_file, 'r') as f:
        for line in f:
            line_list = re.split('[\s]', line)
            if line_list[0] == '<junction':
                id = int(float(line_list[1][4:-1]))
                x = float(line_list[3][3:-1])
                y = float(line_list[4][3:-1])
                junctions_coordinate[id] = [x,y]
    return junctions_coordinate


def edge():
    edge_file = "tiexi_edges.xml"
    edges_line = {} # id:[x,y]
    edges_boundary = {} #id:[junction_id,junction_id]
    with open(edge_file, 'r') as f:
        for line in f:
            line_list = re.split('[\s]', line)
            if line_list[0] == '<edge':
                id = line_list[1][4:-1]
                source = int(float(line_list[2][6:-1]))
                target = int(float(line_list[3][4:-1]))
                edges_boundary[id] = [source, target]
    return edges_boundary


def adjacent(edges_boundary, junctions_coordinate):
    adjacents = {} # id:[neighbor_id, neighbor_id]
    for jun in junctions_coordinate.keys():
        adjacents[jun] = []
    for edge_id, edge_end in edges_boundary.items():
        source = edge_end[0]
        target = edge_end[1]
        if target not in adjacents[source]:
            adjacents[source].append(target)
        if source not in adjacents[target]:
            adjacents[target].append(source)
    return adjacents


def intersection_combination(junctions_coordinate):
    for it1, pos1 in junctions_coordinate.items():
        lis = []
        for it2, pos2 in junctions_coordinate.items():

            if it1 == it2:
                continue
            dis = nndis(pos1[0], pos1[1], pos2[0], pos2[1])
            if dis <= 30:
                lis.append(it2)
        if lis:
            Gp.all_in_one[it1] = lis
    for c, n in Gp.all_in_one.items():
        f = 0
        for l in Gp.intersections_combination:
            if c in l:
                f = 1
        if f == 0:
            x = copy.deepcopy(n)
            x.append(c)
            Gp.intersections_combination.append(x)
            Gp.num += 1
    return

def combination():
    i = 0
    for pair in Gp.intersections_combination:
        Gp.it_comb_detail[i] = pair
        x = 0
        y = 0
        for it in pair:
            x += Gp.intersection[it][0]
            y += Gp.intersection[it][1]
        Gp.it_comb_pos[i] = [round(x/len(pair), 2), round(y/len(pair), 2)]
        i += 1
    Gp.it_pos = copy.deepcopy(Gp.intersection)
    for area in Gp.all_in_one:
        del Gp.it_pos[area]
    Gp.it_pos.update(Gp.it_comb_pos)
    return

def comb_adjacent():
    Gp.adjacents_comb = copy.deepcopy(Gp.adjacents)
    temp = {i:[] for i in range(0,48)}
    for it, detail in Gp.it_comb_detail.items():
        for small_it in detail:
            for neb in Gp.adjacents[small_it]:
                if neb not in temp[it] and neb not in detail:
                    temp[it].append(neb)
            del Gp.adjacents_comb[small_it]
    Gp.adjacents_comb.update(temp)

    for current, neib_set in Gp.adjacents_comb.items():
        for it, detail in Gp.it_comb_detail.items():
            for small_it in detail:
                if small_it in neib_set:
                    if it not in Gp.adjacents_comb[current]:
                        Gp.adjacents_comb[current].append(it)
    for it, detail in Gp.it_comb_detail.items():
        for small_it in detail:
            for current in Gp.adjacents_comb:
                if small_it in Gp.adjacents_comb[current]:
                    Gp.adjacents_comb[current].remove(small_it)
    return

def inter_vehicles_num(node_info_dict, junctions_coordinate, adjacents):
    veh_num = {v: {u: [] for u in adjacents[v]} for v in adjacents.keys()}
    path_length = {v: {u: 0 for u in adjacents[v]} for v in adjacents.keys()}

    for current, adjacent_set in adjacents.items():
        for neighbor in adjacent_set:
            current_x = junctions_coordinate[current][0]
            current_y = junctions_coordinate[current][1]
            neighbor_x = junctions_coordinate[neighbor][0]
            neighbor_y = junctions_coordinate[neighbor][1]
            half = []
            length = nndis(current_x, current_y, neighbor_x, neighbor_y)
            n = 1 + math.ceil(length / Gp.com_dis)
            part_length = length / n
            part_x = abs(current_x - neighbor_x) / n
            part_y = abs(current_y - neighbor_y) / n
            path_length[current][neighbor] = part_length
            if current_x > neighbor_x and current_y < neighbor_y:
                for i in range(0, n+1):
                    x = [current_x - (i+1) * part_x, current_x - i * part_x]
                    y = [current_y + i * part_y, current_y + (i + 1) * part_y]
                    half.append([x, y])
            elif current_x < neighbor_x and current_y < neighbor_y:
                for i in range(0, n):
                    x = [current_x + i * part_x, current_x + (i+1) * part_x]
                    y = [current_y + i * part_y, current_y + (i+1) * part_y]
                    half.append([x, y])
            elif current_x < neighbor_x and current_y > neighbor_y:
                for i in range(0, n+1):
                    x = [current_x + i * part_x, current_x + (i + 1) * part_x]
                    y = [current_y - (i+1) * part_y, current_y - i * part_y]
                    half.append([x, y])
            elif current_x > neighbor_x and current_y > neighbor_y:
                for i in range(0, n+1):
                    x = [current_x - (i + 1) * part_x, current_x - i * part_x]
                    y = [current_y - (i + 1) * part_y, current_y - i * part_y]
                    half.append([x, y])
            else:
                print("存在同轴的道路！")

            if abs(current_x - neighbor_x) > abs(current_y - neighbor_y):
                for value in half:
                    value[1][0] -= 60
                    value[1][1] += 60
            else:
                for value in half:
                    value[0][0] -= 60
                    value[0][1] += 60


            for part in range(0, n):
                num = 0
                for node_id, node_pos in node_info_dict.items():
                    if node_pos[0][0] >= half[part][0][0] and node_pos[0][0] <= half[part][0][1] and node_pos[0][1] >= half[part][1][0] and \
                            node_pos[0][1] <= half[part][1][1]:
                        num += 1
                veh_num[current][neighbor].append(num)
    return veh_num, path_length

def intra_vehicles_num(node_info_dict, junctions_coordinate, adjacents):
    veh_num = {v: [] for v in adjacents.keys()}
    veh_detail = {v: [] for v in adjacents.keys()}
    path_length = {v: [] for v in adjacents.keys()}
    node_area = {node: [] for node in node_info_dict}

    for current, adjacent_set in adjacents.items():
        for neighbor in adjacent_set:
            c_h = []
            current_x = junctions_coordinate[current][0]
            current_y = junctions_coordinate[current][1]
            neighbor_x = junctions_coordinate[neighbor][0]
            neighbor_y = junctions_coordinate[neighbor][1]
            half_x = (current_x + neighbor_x) / 2
            half_y = (current_y + neighbor_y) / 2
            d = nndis(current_x, current_y, half_x, half_y)
            path_length[current].append(d)
            if current_x > neighbor_x and current_y < neighbor_y:
                c_h = [[half_x, current_x], [current_y, half_y]]
            elif current_x < neighbor_x and current_y < neighbor_y:
                c_h = [[current_x, half_x], [current_y, half_y]]
            elif current_x < neighbor_x and current_y > neighbor_y:
                c_h = [[current_x, half_x], [half_y, current_y]]
            elif current_x > neighbor_x and current_y > neighbor_y:
                c_h = [[half_x, current_x], [half_y, current_y]]
            else:
                print("存在同轴的道路！")
            if abs(current_x - neighbor_x) > abs(current_y - neighbor_y):
                c_h[1][0] -= 60
                c_h[1][1] += 60
            else:
                c_h[0][0] -= 60
                c_h[0][1] += 60

            veh_num[current].append(0)
            for node_id, node_pos in node_info_dict.items():
                if node_pos[0][0] >= c_h[0][0] and node_pos[0][0] <= c_h[0][1] and node_pos[0][1] >= c_h[1][0] and \
                        node_pos[0][1] <= c_h[1][1]:
                    if current not in node_area[node_id]:
                        node_area[node_id].append(current)
                    veh_num[current][-1] += 1
                    veh_detail[current].append(node_id)
    return veh_num, veh_detail, path_length, node_area
