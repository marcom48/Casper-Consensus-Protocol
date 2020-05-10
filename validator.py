from block import Block, Dynasty
from message import VoteMessage
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
        self.dependencies = {}

        self.proposed_blocks = []

        # Set of finalised dynasties
        self.finalised_dynasties = set()
        self.finalised_dynasties.add(Dynasty(INITIAL_VALIDATORS, 0))

        # My current epoch
        self.current_height = 0
        # Network I am connected to
        self.network = network
        network.nodes.append(self)
        # Tails are for checkpoint blocks, the tail is the last block
        # (before the next checkpoint) following the checkpoint
        self.tails = {ROOT.hash: ROOT}

        # Closest checkpoint ancestor for each block
        self.tail_membership = {ROOT.hash: ROOT.hash}
        self.id = id

    # If we processed an object but did not receive some dependencies
    # needed to process it, save it to be processed later
    def add_dependency(self, hash_, obj):
        if hash_ not in self.dependencies:
            self.dependencies[hash_] = []
        self.dependencies[hash_].append(obj)

    # Get the checkpoint immediately before a given checkpoint
    def get_checkpoint_parent(self, block):

        # Genesis
        if block.height == 0:
            return None

        return self.processed[self.tail_membership[block.parent_hash]]

    def is_ancestor(self, ancestor, descendant):
        """Is a given checkpoint an ancestor of another given checkpoint?
        Args:
            anc: ancestor block (or block hash)
            desc: descendant block (or block hash)
        """
        # if anc or desc are block hashes, we can get the blocks from self.processed
        if not isinstance(ancestor, Block):
            ancestor = self.processed[ancestor]

        if not isinstance(descendant, Block):
            descendant = self.processed[descendant]

        # Check that the blocks are both checkpoints
        assert ancestor.height % EPOCH_SIZE == 0
        assert descendant.height % EPOCH_SIZE == 0

        while True:
            if descendant is None:
                return False
            if descendant.hash == ancestor.hash:
                return True
            descendant = self.get_checkpoint_parent(descendant)


    def slash(self):
        
        if not self.slashed:
            print("SLASHING")
            x = self.deposit * 0.2
            self.deposit -= x
            self.slashed = True
            print(f"{self.id}, {self.deposit}")
            return x
        return 0

    def reward(self):
        
        x = self.deposit * 0.1
        self.deposit += x
        return x


    # Called every round
    def tick(self, time):
        # At time 0: validator 0
        # At time BLOCK_PROPOSAL_TIME: validator 1
        # .. At time NUM_VALIDATORS * BLOCK_PROPOSAL_TIME: validator 0
        if self.id == (time // BLOCK_PROPOSAL_TIME) % NUM_VALIDATORS and time % BLOCK_PROPOSAL_TIME == 0:

            # One node is authorized to create a new block and broadcast it
            new_block = Block(self.head, self.finalised_dynasties)
            self.proposed_blocks.append(new_block)

            self.network.broadcast(new_block)
            # immediately "receive" the new block (no network latency)
            self.on_receive(new_block)
