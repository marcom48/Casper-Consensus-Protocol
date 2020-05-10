import random
import utils
from parameters import *


class Block():
    """One node (roundrobin) adds a new block to the blockchain every
    BLOCK_PROPOSAL_TIME iterations.

    Args:
        parent: parent block
        finalised_dynasties: dynasties which have been finalised.
                             Only a committed block's dynasty becomes finalised.
    """

    def __init__(self, parent=None, finalised_dynasties=None):
        """A block contains the following arguments:

        self.hash: hash of the block
        self.height: height of the block (genesis = 0)
        self.parent_hash: hash of the parent block
        self.rear_validators: previous dynasty (2/3 have to commit)
        self.forward_validators: current dynasty (2/3 have to commit)
        self.next_dynasty: next dynasty

        The block needs to be signed by both the previous and current dynasties.
        The next dynasty is decided at this block so that it is public.
        """
        self.hash = utils.generate_hash()

        # Genesis block
        if not parent:
            
            self.height = 0

            self.parent_hash = 0
            
            # Rear and forward validators equal
            self.rear_validators = self.forward_validators = BlockDynasty(
                INITIAL_VALIDATORS, 0)
            
            self.next_dynasty = self.generate_next_dynasty(
                self.forward_validators.id)
        else:

            self.height = parent.height + 1
            self.parent_hash = parent.hash

            # Generate a random next dynasty
            self.next_dynasty = self.generate_next_dynasty(
                parent.forward_validators.id)

            # If the forward_validators was finalised, we advance to the next dynasty
            
            if parent.forward_validators in finalised_dynasties:
                self.rear_validators = parent.forward_validators
                self.forward_validators = parent.next_dynasty

            else:  # `forward_validators` has not yet been finalised so we don't rotate validators
                self.rear_validators = parent.rear_validators
                self.forward_validators = parent.forward_validators

        self.is_checkpoint = self.height % EPOCH_SIZE == 0
        self.checkpoint_height = self.height // EPOCH_SIZE

    def generate_next_dynasty(self, rear_validators_id):
        # Fix the seed so that every validator can generate the same dynasty
        random.seed(self.hash)
        next_dynasty = BlockDynasty(random.sample(
            VALIDATOR_IDS, NUM_VALIDATORS), rear_validators_id + 1)

        # Remove the seed for other operations
        random.seed()
        return next_dynasty


class BlockDynasty():

    def __init__(self, validators, _id):
        self.validators = validators
        self.id = _id

    def __hash__(self):
        return hash(str(self.id) + str(self.validators))

    def __eq__(self, other):
        return (str(self.id) + str(self.validators)) == \
               (str(other.id) + str(other.validators))
