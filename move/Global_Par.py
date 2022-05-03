
total_node_num = [1000, 1500, 2000, 2500, 3000]
comb_node_num = [800, 1200, 1600, 2000, 2400]


map_boundary = [46, 7, 38, 811022916]


biaoji = 0
delay_hop_tag = 0

intersection = {}
adjacents = {}
edges_boundary = {}


all_in_one = {}
intersections_combination = []
it_comb_detail = {}
it_comb_pos = {}
num = 0

it_pos = {}
adjacents_comb = {}



com_dis = 350


un_intersections = [26, 1501191067, 1554161759, 1554162236, 3011987317, 3011958556, 34, 3011970566, 32, 1774678167, 677603150, 1776032723, 6395814545, 18, 0, 5377474182, 1774638801, 6395814548, 2043972045, 5268439719, 1585713352, 28, 1585713348, 19, 2043972058, 1, 6110489165, 6110489168, 6110489172, 25, 27, 4340744995, 4537420835, 29, 5267470789, 5267470788, 4537420815, 4537420818, 4537420819, 4537420821]

com_node_rate = 0.2

update_period = 1

sum = 0
record = []
effi = 0
MAX = 600000

re_time = 3


pkt_delay = []
pkt_delay_800 = []
pkt_delay_1600 = []
pkt_delay_2400 = []
pkt_delay_3200 = []
hop_list = []
hop_list_800 = []
hop_list_1600 = []
hop_list_2400 = []
hop_list_3200 = []
total_pkt_delay = {}
total_pkt_delay_800 = {}
total_pkt_delay_1600 = {}
total_pkt_delay_2400 = {}
total_pkt_delay_3200 = {}
total_hop_list = {}
total_hop_list_800 = {}
total_hop_list_1600 = {}
total_hop_list_2400 = {}
total_hop_list_3200 = {}
success_time = 0
success_0_800 = 0
success_800_1600 = 0
success_1600_2400 = 0
success_2400_3200 = 0
fail_time = 0
loop_fail_time = 0
test_loop_fail_time = 0
success_time_list = []
success_0_800_list = []
success_800_1600_list = []
success_1600_2400_list = []
success_2400_3200_list = []
fail_time_list= []
loop_file_time_list = []
test_loop_fail_time_list = []

overhead = []
overhead_list = {}
overhead_index = 0
test_num = []
total_test_num = {}
test_success = []
N = 5
delay_veh_processing = 1
delay_bs_processing = 1
delay_up_down = 1
constant_strength = N * (delay_veh_processing + delay_bs_processing + delay_up_down)
distribution_record = []
connectivity_record = []
distance_record = []
normalized_distribution_record = []
normalized_connectivity_record = []
normalized_distance_record = []
distance_a = 1
distance_b = 0
nor_para_seq = 0
distance_min = [0.15774859284379994, 0.15774859284379994, 0.15774859284379994, 0.15774859284379994, 0.15774859284379994]
distance_max = [2.012700464538705, 2.012700464538705, 2.012700464538705, 2.012700464538705, 2.012700464538705]
distance_var = [0.16562740095073933, 0.16562740095073933, 0.16562740095073933, 0.16562740095073933, 0.16562740095073933]
connectivity_min = [0.0, 0.0, 0.0, 0.0, 0.0]
connectivity_max = [0.13557349860623996, 0.16462165924051375, 0.18465087716246717, 0.19837549834951584, 0.2580033870465819]
distribution_min = [0.0, 0.0, 0.0, 0.0, 0.0]
distribution_max = [0.14309068246223333, 0.15397449745231395,  0.15397449745231395, 0.22521774788279159, 0.22521774788279159]
distribution_var = [0.015772824078035194, 0.019545574104876257, 0.02338558433596064, 0.028496788175371233, 0.032770350221516226]
distance_close_a = 0
distance_close_b = 0
distance_medium_a = 0
distance_medium_b = 0
distance_medium_c = 0
distance_medium_d = 0
distance_far_a = 0
distance_far_b = 0
connectivity_low_a = 0
connectivity_low_b = 0
connectivity_middle_a = 0
connectivity_middle_b = 0
connectivity_middle_c = 0
connectivity_middle_d = 0
connectivity_high_a = 0
connectivity_high_b = 0
distribution_poor_a = 0
distribution_poor_b = 0
distribution_medium_a = 0
distribution_medium_b = 0
distribution_medium_c = 0
distribution_medium_d = 0
distribution_good_a = 0
distribution_good_b = 0
q_alpha = 0.3
q_gamma = 0.1
positive_a = 0.3
positive_b = 0.3
positive_c = 0.4
negative_a = 0.7
negative_b = 0.7