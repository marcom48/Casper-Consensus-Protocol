from block import Block
from network import VoteMessage
from parameters import *
from collections import defaultdict

# Root of the blockchain
ROOT = Block()

class Validator(object):
    """Abstract class for validators."""

    def __init__(self, network, _id):

        self.id = _id
        self.received = {ROOT.hash: ROOT}

        self.message_buffer = {}

        self.proposed_blocks = []

        # Current working height in tree.
        self.current_height = 0

        
        self.network = network
        self.network.register(self)
        
        # Path are for checkpoints, the value is last block before next checkpoint.
        self.paths = {ROOT.hash: ROOT}

        # Closest checkpoint ancestor for each block.
        self.path_membership = {ROOT.hash: ROOT.hash}
        

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
        
        if not self.slashed:
            #print(f"Slashing validator {self.id}")
            x = self.deposit * 0.2
            self.deposit -= x
            self.slashed = True
            ##print(f"{self.id}, {self.deposit}")
            return x
        return 0

    def reward(self):
        #print(f"Rewarding validator {self.id}")
        x = self.deposit * 0.1
        self.deposit += x
        return x


    # Called every round
    def tick(self, time):
        
        # Generate block.
        if self.id == (time // BLOCK_PROPOSAL_TIME) % NUM_VALIDATORS and time % BLOCK_PROPOSAL_TIME == 0:

            # One node is authorized to create a new block and broadcast it
            new_block = Block(self.head)
            self.proposed_blocks.append(new_block)

            self.network.broadcast(new_block)
            #print(f"Validator {self.id} proposing block{new_block.hash}")
            
            
            self.deliver(new_block)
