

from other import *
import numpy as np
from _collections import deque


class ENV:
    def __init__(self, num_md, num_task, num_bs):
        self.num_md = num_md
        self.num_task = num_task
        self.num_bs = num_bs
        self.md = get_md_info(num_md)
        self.task = get_task_info(num_task)
        self.bs = get_bs_info(num_bs)
        self.fmax = 3200
        self.is_off = [0] * num_task
        self.alloc_resource = [0] * num_task
        self.rest_resource = [0] * num_bs
        i = 0
        while i < num_bs:
            self.rest_resource[i] = self.bs[i].cpu_frequency
            i += 1
        self.progress = [0] * num_task
        self.done = False
        self.waiting = deque()
        self.new_queue = 0
        self.count_wrong = 0
        self.time = 0

    def get_init_state(self):
        self.count_wrong = 0
        self.time = 0
        self.is_off = [0] * self.num_task
        self.alloc_resource = [0] * self.num_task
        i = 0
        while i < self.num_bs:
            self.rest_resource[i] = self.bs[i].cpu_frequency
            i += 1
        self.progress = [0] * self.num_task
        self.new_task()
        state = np.concatenate((self.is_off, self.progress, self.alloc_resource, self.rest_resource))
        return state

    def new_task(self):
        self.waiting.clear()
        rest = self.num_task - sum(self.progress)
        length = random.randint(1, self.num_bs) if rest >= self.num_bs else rest
        task_id = sum(self.progress)
        self.waiting.extend(range(task_id, task_id + length))
        self.new_queue = 1

    def all_local(self):
        i = 1
        cost = 0
        while i <= self.num_task:
            cost += self.task[i].cpu_cycles / self.md[self.task[i].md].cpu_frequency
            i += 1
        return cost

    def step(self, action):
        i = 0
        while i < 3:
            if action[i] > 1: action[i] = 1
            if action[i] < -1: action[i] = -1
            i += 1


        get1 = 1 if action[0] > 0 else 0
        get2 = int((action[1] + 1) * (self.num_bs - 1) / 2)
        get3 = int((action[2] + 1) * 2000 / 2) + 1000

        i_task = self.waiting[0]
        i_md = self.task[i_task].md
        T = self.task[i_task].delay_constraints

        if self.new_queue == 1:
            i = 0
            while i < self.num_bs:
                self.rest_resource[i] = self.bs[i].cpu_frequency
                i += 1

        if get1 == 0:
            f = self.md[i_md].cpu_frequency
            t = self.task[i_task].cpu_cycles / f

            if t <= T:
                self.is_off[i_task] = 0
                self.progress[i_task] = 1
                self.alloc_resource[i_task] = f
                self.done = True if sum(self.progress) == self.num_task else False
                reward = T - t
                self.waiting.popleft()
                self.time += t
            else:
                self.waiting.popleft()
                reward = -T
                self.progress[i_task] = 1
                self.done = True if sum(self.progress) == self.num_task else False
                self.count_wrong += 1
                self.time += T


        else:
            f = get3
            v = 2
            t = self.task[i_task].data_size / v + self.task[i_task].cpu_cycles / f
            if f <= self.rest_resource[get2] and t <= T:
                self.is_off[i_task] = get2 + 1
                self.progress[i_task] = 1
                self.alloc_resource[i_task] = f
                self.rest_resource[get2] -= f
                self.done = True if sum(self.progress) == self.num_task else False
                reward = T - t
                self.waiting.popleft()
                self.time += t
            else:
                self.waiting.popleft()
                reward = -T
                self.progress[i_task] = 1
                self.done = True if sum(self.progress) == self.num_task else False
                self.count_wrong += 1
                self.time += T
        if self.waiting:
            self.new_queue = 0
        else:
            self.new_task()
            self.new_queue = 1
        state = np.concatenate((self.is_off, self.progress, self.alloc_resource, self.rest_resource))
        return state, reward, self.done
