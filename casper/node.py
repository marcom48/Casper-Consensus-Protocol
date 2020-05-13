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


    # Add messages to a buffer for later processing.
    def add_message_buffer(self, hash_, obj):
        if hash_ not in self.message_buffer:
            self.message_buffer[hash_] = []
        self.message_buffer[hash_].append(obj)


    # Get the checkpoint immediately before a given checkpoint
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
        
        x = self.deposit * SLASH
        self.deposit -= x
        return x

    def reward(self):
        #print(f"Rewarding validator {self.id}")
        x = self.deposit * REWARD
        self.deposit += x
        return x


    def execute(self, time):
        
        # Generate block.
        if self.id == (time // BLOCK_FREQUENCY) % VALIDATORS and time % BLOCK_FREQUENCY == 0:

            # One node is authorized to create a new block and broadcast it
            new_block = Block(self.head)
            self.proposed_blocks.append(new_block)

            self.network.broadcast(new_block, self.id)
            #print(f"Validator {self.id} proposing block{new_block.hash}")
            
            
            self.deliver(new_block)
