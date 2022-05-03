
import Node as Nd
import SDVN_Controller as Sc
import random
def init_node(node_id_position, controller):
    node_list = []
    for i in range(node_id_position.shape[0]):
        node_list.append(Nd.Node(int(node_id_position[i][0, 0]), controller))
    return node_list


def init_controller(node_num, intersection):
    return Sc.SDVNController(node_num, intersection)

# 获取通信的节点，得到n对 数据包收/发节点（自写）
def get_communication_node(node_num, n):
    com_nodelist = [] # 通信节点列表
    #error = [0,2,6,56,61] #失效节点id
    while True:
    # for i in range(node_num):
        if len(com_nodelist) < n:
            # random.random()生成0和1之间的随机浮点数float
            node1_id = round(random.random() * node_num)   # 随机生成一个节点id
            node2_id = round(random.random() * node_num)
            #if node1_id not in error and node2_id not in error:
            com_nodelist.append([node1_id, node2_id])
        else: # 通信节点列表已满，结束
            break
    # 返回 n/2 对通信节点
    return com_nodelist