import random
from parameters import *
import utils

class Network(object):
    """Networking layer controlling the delivery of messages between nodes.

    self.msg_arrivals is a table where the keys are the time of arrival of
        messages and the values is a list of the objects received at that time
    """

    def __init__(self, _latency):
        self.nodes = []
        self.time = 0
        self.msg_arrivals = {}
        self.latency = _latency

        self.total_deposit = INITIAL_DEPOSIT * NUM_VALIDATORS


    def register(self, node):
        self.nodes.append(node)


    def generate_latency(self):
        return 1 + int(random.expovariate(1) * self.latency)

    def slash_node(self, node):
        for n in self.nodes:
            if n.id == node:
                if not n.slashed:
                    self.total_deposit -= n.slash()
                break

    
    def reward_node(self, node):
        for n in self.nodes:
            if n.id == node:
                self.total_deposit += n.reward()
                break

    def broadcast(self, msg):
        """

        Prepares a message to be broadcast to the nodes.
        Each message is prepared with an actual delivery time, and is sent
        when tick() is called.

        """

        for node in self.nodes:
            # Create a different delay for every receiving node i
            # Delays need to be at least 1
            delay = self.generate_latency()

            deliver_time = self.time + delay
            if not self.msg_arrivals.get(deliver_time):
                self.msg_arrivals[deliver_time] = []

            self.msg_arrivals[deliver_time].append((node.id, msg))

    def tick(self):
        """Simulates a tick of time.

        """

        # If there are messages to be sent at this time
        if self.time in self.msg_arrivals:

            for node_index, msg in self.msg_arrivals[self.time]:

                self.nodes[node_index].deliver(msg)

            del self.msg_arrivals[self.time]

        # Simulate time tick across each node
        for n in self.nodes:

            n.tick(self.time)

        self.time += 1


class VoteMessage():

    def __init__(self, source, target, source_height, target_height, validator, deposit):
        self.source = source
        self.target = target
        self.source_height = source_height
        self.target_height = target_height
        self.validator = validator
        self.hash = utils.generate_hash()
        self.deposit = deposit

    def __str__(self):
        return f'{self.source_height}, {self.target_height}, {self.validator}'
