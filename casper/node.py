'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063
'''

from casper.block import Block
from casper.network import VoteMessage
from helper.parameters import *
from collections import defaultdict

# Create root.
GENESIS = Block()

class Node(object):
    '''
    Class defining bare requirements for
    a node in the blockchain network.
    '''

    def __init__(self, network, _id):

        self.id = _id
        self.received = {GENESIS.hash: GENESIS}
        # self.received = {}

        self.message_buffer = {}

        self.proposed_blocks = []
        self.proposed_votes = []

        # Current working height in tree.
        self.current_height = 0

        
        self.network = network
        self.network.register(self)
        
        # Path are for checkpoints, the value is last block before next checkpoint.
        self.paths = {GENESIS.hash: GENESIS}

        # Closest checkpoint ancestor for each block.
        self.path_membership = {GENESIS.hash: GENESIS.hash}

        self.slashed = False

        self.has_finalised = False
        
        self.byzantine = False


    def add_message_buffer(self, hash_, obj):
        '''
        Add messages to a buffer for later processing.
        '''
        if hash_ not in self.message_buffer:
            self.message_buffer[hash_] = []
        self.message_buffer[hash_].append(obj)


    def get_checkpoint_parent(self, block):

        # Genesis
        if block.height == 0:
            return None

        return self.received[self.path_membership[block.parent_hash]]

    def is_ancestor(self, ancestor, descendant):

        # Get blocks via hash if provided.
        if not isinstance(ancestor, Block):
            ancestor = self.received[ancestor]

        if not isinstance(descendant, Block):
            descendant = self.received[descendant]

        while True:
            if descendant is None:
                return False
            if descendant.hash == ancestor.hash:
                return True
            descendant = self.get_checkpoint_parent(descendant)


    def slash(self):
        
        slash_amount = self.deposit * SLASH
        self.deposit -= slash_amount
        return slash_amount

    def reward(self):
        reward_amount = self.deposit * REWARD
        self.deposit += reward_amount
        return reward_amount


    def execute(self, time):
        '''
        Function simulates a unit of time passing in the validator.
        '''

        # Generate block for round robin.
        if self.id == (time // BLOCK_FREQUENCY) % VALIDATORS and time % BLOCK_FREQUENCY == 0:

            new_block = Block(self.head)

            self.proposed_blocks.append(new_block)

            self.network.broadcast(new_block, self.id)
            
            self.deliver(new_block)
