from math import *
import Global_Par as Gp

def getdis(ax, ay, bx, by):
    temp_x = ax - bx
    temp_y = ay - by
    temp_x = temp_x * temp_x
    temp_y = temp_y * temp_y
    result = sqrt(temp_x+temp_y)
    return result

def angle(x1, y1, x2, y2):
    line_len = sqrt((x2-x1)**2 + (y2-y1)**2)
    if line_len == 0:
        # print("2 nodes are the same\n")
        return 0
    sin_theta = (y2-y1)/line_len
    cos_theta = (x2-x1)/line_len
    theta = acos(cos_theta)
    if sin_theta < 0:
        theta = 2*pi - theta
    return theta

def intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    if min(x1, x2)<=max(x3, x4) and min(x3, x4)<=max(x1, x2) and \
        min(y1, y2)<=max(y3, y4) and min(y3, y4)<=max(y1, y2):

        u = (x3-x1)*(y2-y1) - (x2-x1)*(y3-y1)
        v = (x4-x1)*(y2-y1) - (x2-x1)*(y4-y1)
        w = (x1-x3)*(y4-y3) - (x4-x3)*(y1-y3)
        z = (x2-x3)*(y4-y3) - (x4-x3)*(y2-y3)
        if u*v <0 and w*z<0:
            return 1
    return 0

def gf_nexthop(node_id, neib_list, des_id, node_list):
    current = node_list[node_id]
    destination = node_list[des_id]
    nexthop = -1
    mindis = getdis(current.position[0], current.position[1], destination.position[0], destination.position[1])
    for node in neib_list:
        nx = node_list[node].position[0]
        ny = node_list[node].position[1]
        tempdis = getdis(nx, ny, destination.position[0], destination.position[1])
        if tempdis < mindis:
            mindis = tempdis
            nexthop = node
    return nexthop


def gg_planarize(node_id, neib_list, node_list):
    result = []
    current = node_list[node_id]
    for node in neib_list:
        flag = 1
        midpx = current.position[0] + (node_list[node].position[0] - current.position[0])/2
        midpy = current.position[1] + (node_list[node].position[1] - current.position[1])/2
        mdis = getdis(current.position[0], current.position[1], midpx, midpy)
        for other in neib_list:
            if node_list[other].node_id != node_list[node].node_id:
                tempdis = getdis(midpx, midpy, node_list[other].position[0], node_list[other].position[1])
                if tempdis < mdis:
                    flag = 0
                    break
        if flag == 1:
            result.append(node)
    return result


def peri_nexthop(node_id, neib_list, des_id, node_list, last):
    current = node_list[node_id]
    destination = node_list[des_id]

    nexthop = node_id
    planar_neighbors = gg_planarize(node_id, neib_list, node_list)
    if last > -1:
        lastnb = node_list[last]
        if lastnb == None:
            print("Wrong last nb %d -> %d \n" % (last, node_id))
            return -1
        alpha = angle(current.position[0], current.position[1], node_list[last].position[0], node_list[last].position[1]) # 计算当前节点与上一跳节点连线的夹角
    else:
        alpha = angle(current.position[0], current.position[1], destination.position[0], destination.position[1]) # 计算当前节点与目的节点的连线
    minagle = 10000
    for temp_id in planar_neighbors:
        temp = node_list[temp_id]
        if temp.node_id != last:
            delta = angle(current.position[0], current.position[1], temp.position[0], temp.position[1])
            delta = delta - alpha
            if delta < 0.0 :
                delta = 2*pi + delta
            if delta < minagle:
                minagle = delta
                nexthop = temp.node_id
    next = node_list[nexthop]
    if next == None:
        return -1
    return nexthop

def find_next(node_id, neib_list, des_id, node_list):
    forward_type = 0
    current = node_list[node_id]
    destination = node_list[des_id]
    if Gp.forward_type != 2:
        nexthop = peri_nexthop(node_id, neib_list, des_id, node_list, -1)
        Gp.forward_type -= 1

    else:
        mindis = getdis(current.position[0], current.position[1], destination.position[0], destination.position[1])
        for neib in neib_list:
            dis = getdis(node_list[neib].position[0], node_list[neib].position[1], destination.position[0], destination.position[1])
            if dis<mindis:
                forward_type = 1
                break
        if forward_type == 1:
            nexthop = gf_nexthop(node_id, neib_list, des_id, node_list)
        else:
            nexthop = peri_nexthop(node_id, neib_list, des_id, node_list, -1)
            Gp.forward_type -= 1
    if Gp.forward_type == 0:
        Gp.forward_type = 2
    return nexthop

