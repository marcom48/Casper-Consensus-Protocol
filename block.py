import random
import utils
from parameters import *


class Block():


    def __init__(self, parent=None):
        
        # Genesis block
        if not parent:
            
            self.height = 0

            self.parent_hash = 0

        else:
            # Increase from parent
            self.height = parent.height + 1
            self.parent_hash = parent.hash

        # Rear and forward validators equal
        self.validators = INITIAL_VALIDATORS

        self.hash = utils.generate_hash()
        
        self.is_checkpoint = self.height % EPOCH_SIZE == 0
        
        self.checkpoint_height = self.height // EPOCH_SIZE


