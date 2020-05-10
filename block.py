import utils
from parameters import VALIDATOR_IDS, CHECKPOINT_DIFF


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

        
        self.validators = VALIDATOR_IDS

        self.hash = utils.generate_hash()
        
        self.is_checkpoint = self.height % CHECKPOINT_DIFF == 0
        
        self.checkpoint_height = self.height // CHECKPOINT_DIFF
