from block import Block
from network import VoteMessage
from parameters import *

# Root of the blockchain
ROOT = Block()

class Validator(object):
    """Abstract class for validators."""

    def __init__(self, network, id):
        # processed blocks
        self.processed = {ROOT.hash: ROOT}

        # Messages that are not processed yet, and require another message
        # to be processed
        # Dict from hash of dependency to object that can be processed
        # when dependency is processed
        # Example:
        # prepare messages processed before block is processed
        # commit messages processed before we reached 2/3 prepares

        # Looks to be anything that isn't finished.
        self.buffer = {}

        self.proposed_blocks = []

        # Current height validator is building on.
        self.current_height = 0

        self.network = network

        network.register(self)

        # Tails are for checkpoint blocks, the tail is the last block
        # (before the next checkpoint) following the checkpoint
        self.tails = {ROOT.hash: ROOT}

        # Closest checkpoint ancestor for each block
        self.tail_membership = {ROOT.hash: ROOT.hash}
        
        self.id = id

    # If we processed an object but did not receive some buffer
    # needed to process it, save it to be processed later
    def add_to_buffer(self, _hash, obj):
        
        # Assert not already in buffer.
        if _hash not in self.buffer:
            self.buffer[_hash] = [obj]
        else:
                    
            self.buffer[_hash].append(obj)

    # Get the checkpoint immediately before a given checkpoint
    def get_checkpoint_parent(self, block):

        # Genesis
        if block.height == 0:
            return None

        return self.processed[self.tail_membership[block.parent_hash]]

    def is_ancestor(self, ancestor, descendant):
        
        # Get block via hash if provided.
        if not isinstance(ancestor, Block):
            ancestor = self.processed[ancestor]

        if not isinstance(descendant, Block):
            descendant = self.processed[descendant]

        while True:
            if descendant is None:
                return False
            if descendant.hash == ancestor.hash:
                return True
            descendant = self.get_checkpoint_parent(descendant)

    # Slash a validator.
    def slash(self):
        
        if not self.slashed:
            # Reduce by 10%
            x = self.deposit * 0.1
            self.deposit -= x

            # Mark as slashed for current Byzantine message.
            # PERHAPS ADD DICT WITH MESSAGE AS KEY TO MARK AS SLASHED FOR THAT MESSAGE
            self.slashed = True
            
            return x
        return 0

    # Reward a validator.
    def reward(self):
        
        x = self.deposit * 0.1
        self.deposit += x
        return x


    # Called every round
    def tick(self, time):
        
        # Propose a new block.
        if self.id == (time // BLOCK_PROPOSAL_TIME) % NUM_VALIDATORS and time % BLOCK_PROPOSAL_TIME == 0:

            
            new_block = Block(self.head)
            
            self.proposed_blocks.append(new_block)

            self.network.broadcast(new_block)
            
            # No latency to self.
            self.deliver(new_block)
