import random
from message import VoteMessage


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

    def add_nodes(self, _nodes):
        self.nodes = _nodes

    def generate_latency(self):
        return 1 + int(random.expovariate(1) * self.latency)

    def broadcast(self, msg):
        """

        Prepares a message to be broadcast to the nodes.
        Each message is prepared with an actual delivery time, and is sent
        when tick() is called.

        """
        if isinstance(msg, VoteMessage):
            print(f"Network {msg}")
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

                self.nodes[node_index].on_receive(msg)

            del self.msg_arrivals[self.time]

        # Simulate time tick across each node
        for n in self.nodes:

            n.tick(self.time)

        self.time += 1
