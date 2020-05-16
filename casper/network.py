'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063
'''

import random
from helper.parameters import *
from helper.hash_gen import generate_hash
from casper.block import Block
from collections import defaultdict


class Network(object):
    '''
    Network class to simulate the
    blockchain environment.
    '''

    def __init__(self, _latency):

        self.validators = []
        self.time = 0
        self.messages = defaultdict(list)
        self.latency = _latency

        self.to_reward = set()
        self.to_slash = set()

        self.root = Block()

        # Total sum of deposits across validators.
        self.total_deposit = INITIAL_DEPOSIT * VALIDATORS


    def register(self, validators):
        self.validators.append(validators)


    def generate_latency(self):
        return 1 + int(random.expovariate(1) * self.latency)

    def slash_node(self, node):
        self.to_slash.add(node)

   
    def reward_node(self, node):
        self.to_reward.add(node)


    def broadcast(self, msg, node_id):       
        '''
        Function broadcasts a message to validators
        in the network with varying latencies.
        '''

        for node in self.validators:
            
            if node == node_id:
                continue

            # Create delay
            delay = self.generate_latency()

            deliver_time = self.time + delay

            self.messages[deliver_time].append((node.id, msg))

    def execute(self):
        '''
        Function simulates the passage of
        a unit of time throughout the network.
        '''

        # Check for messages to be sent
        if self.time in self.messages:

            for _id, msg in self.messages[self.time]:

                self.validators[_id].deliver(msg)

            # Remove messages
            del self.messages[self.time]

        for node in self.validators:

            node.execute(self.time)


        # Reward and slash nodes.
        for node in list(self.to_reward):
            self.total_deposit += self.validators[node].reward()
        
        for node in list(self.to_slash):
            self.total_deposit -= self.validators[node].slash()

        self.to_reward.clear()
        self.to_slash.clear()

        self.time += 1


class VoteMessage():
    '''
    Class contains structure for votes through network.
    '''
    def __init__(self, source, target, source_height, target_height, validator, deposit):
        self.source = source
        self.target = target
        self.source_height = source_height
        self.target_height = target_height

        # Validator ID.
        self.validator = validator
        
        # Unique hash for vote.
        self.hash = generate_hash()
        
        # Deposit from validator.
        self.deposit = deposit

