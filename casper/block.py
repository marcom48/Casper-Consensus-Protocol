'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063
'''

from  helper.hash_gen import generate_hash
from helper.parameters import *

class Block():

    '''
    Block class for blockchain.
    '''

    def __init__(self, parent=None):

        # Genesis block
        if not parent:
            
            self.height = 0
            self.parent_hash = 0

        else:
            # Increase from parent
            self.height = parent.height + 1
            self.parent_hash = parent.hash

        self.validators = list(range(VALIDATORS))

        self.hash = generate_hash()
        
        self.is_checkpoint = self.height % CHECKPOINT_DIFF == 0
        
        self.checkpoint_height = self.height // CHECKPOINT_DIFF
