'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063
'''

from casper.block import Block
from casper.network import VoteMessage
from helper.parameters import *
from casper.node import GENESIS, Node
from helper.hash_gen import generate_hash
import math, random

class CasperValidator(Node):
    '''
    Class implements the Casper protocol
    to justify and finalise blocks in a simulated
    blockchain network.
    '''

    def __init__(self, network, id):
        super(CasperValidator, self).__init__(network, id)

        self.head = GENESIS

        self.deposit = INITIAL_DEPOSIT

        self.highest_justified_checkpoint = GENESIS

        self.main_chain_size = 1


        # Justified checkpoints.
        self.justified_checkpoints = {GENESIS.hash}

        # Finalised checkpoints
        self.finalised_checkpoints = {GENESIS.hash}

        # Votes from all validators in network.
        self.validator_votes = {}

        # Record of votes for blocks.
        self.block_vote_count = {}


    # Check if block is justified.
    def is_justified(self, _hash):
        return (_hash in self.justified_checkpoints) and (_hash in self.received) and (self.received[_hash].is_checkpoint)

    # Check if block is finalised.
    def is_finalised(self, _hash):
        return (_hash in self.finalised_checkpoints) and (_hash in self.received) and (self.received[_hash].is_checkpoint)


    def accept_block(self, block):
        '''
        Function processes a received block and determines whether to vote to add
        it to the chain or not.
        '''

        # Haven't recieved block's parent.
        if block.parent_hash not in self.received:
            self.add_message_buffer(block.parent_hash, block)
            return False

        
        self.received[block.hash] = block

        if block.is_checkpoint:

            #  Start a tail object for it
            self.path_membership[block.hash] = block.hash
            self.paths[block.hash] = block

            # Create vote
            self.create_vote(block)

        else:

            # Assert in tail
            assert block.parent_hash in self.path_membership

            # Update block's tail to match its parent.
            self.path_membership[block.hash] = self.path_membership[block.parent_hash]

            curr_tail = self.path_membership[block.hash]

            # Adjust end of tail.
            if block.height > self.paths[curr_tail].height:
                self.paths[curr_tail] = block
        
        # Assert in correct tree.
        if self.is_ancestor(self.highest_justified_checkpoint, self.path_membership[block.hash]):
            
            # Update current working head.
            self.head = block
            self.main_chain_size += 1

        else:
            
            # Change path to find current highest head.
            self.fix_head(block)

        return True
 
    def fix_head(self, block):
        '''
        Adjust current working chain head to highest checkpointed block.
        '''

        max_height = self.highest_justified_checkpoint.height
        max_descendant = self.highest_justified_checkpoint.hash
  
        descendants = list(self.paths.keys()).copy()        

        descendants = list(filter(lambda a: self.is_ancestor(
            self.highest_justified_checkpoint, a), descendants))

        # Sort tails by ascending height.
        descendants.sort(key=lambda a: -self.received[a].height)

        highest_desc = max(descendants, key = lambda a: self.received[a].height)

        # Update current height to highest.
        if self.received[highest_desc].height > max_height:
            self.main_chain_size = self.received[highest_desc].height
            self.head = self.received[highest_desc]


    def create_vote(self, block):
        '''
        Function creates and submits a vote for a block to the
        validators in the network.
        '''


        # Create blocks for supermajority link vote.
        target_block = block
        source_block = self.highest_justified_checkpoint

        # Assert creating a block for a new height.
        if target_block.checkpoint_height > self.current_height:


            # Adjust current working height.
            self.current_height = target_block.checkpoint_height

            if self.is_ancestor(source_block, target_block):
                

                if self.byzantine and len(self.proposed_votes) > 0:

                    n = len(self.proposed_votes)

                    # Submit random previous vote to violate slashing condition 1.
                    vote = self.proposed_votes[random.randint(0, n-1)]

                    # Update hash so doesn't appear as duplicate message.
                    vote.hash = generate_hash()
                                
                else:
                    vote = VoteMessage(source_block.hash,
                                target_block.hash,
                                source_block.checkpoint_height,
                                target_block.checkpoint_height,
                                self.id, self.deposit)

                self.proposed_votes.append(vote)
                self.network.broadcast(vote, self.id)
                self.deliver(vote)
                


    def slashing_conditions(self, new_vote):
        '''
        Function determines if a validators has violated the 
        Casper slashing conditions.
        '''
        for past_vote in self.validator_votes[new_vote.validator]:

            # Slashing condition 1.
            if past_vote.target_height == new_vote.target_height:
                return False

            # Slashing condition 2.
            if ((past_vote.source_height < new_vote.source_height and
                 past_vote.target_height > new_vote.target_height) or
               (past_vote.source_height > new_vote.source_height and
                 past_vote.target_height < new_vote.target_height)):
                return False

        return True

    def check_vote(self, vote):
        '''
        Function asserts whether a received vote is a valid vote.
        If enough votes have been received for the relevant block,
        the block is justified.
        '''


       # Haven't received source block yet.
        if vote.source not in self.received:
            self.add_message_buffer(vote.source, vote)

        # Assert source is justified.
        if vote.source not in self.justified_checkpoints:
            return False

        # Haven't received target block.
        if vote.target not in self.received:
            self.add_message_buffer(vote.target, vote)
            return False

        # Assert source is ancestor of target.
        if not self.is_ancestor(vote.source, vote.target):
            return False

        # Create new record for validator if unseen.
        if vote.validator not in self.validator_votes:
            self.validator_votes[vote.validator] = []

        # Check the slashing conditions,
        if not self.slashing_conditions(vote):
            self.network.slash_node(vote.validator)
            return False

        # Valid vote, add to record for validator.
        self.validator_votes[vote.validator].append(vote)

        # Create block vote record.
        if vote.source not in self.block_vote_count:
            self.block_vote_count[vote.source] = {}

        # Update votes
        self.block_vote_count[vote.source][vote.target] = self.block_vote_count[
            vote.source].get(vote.target, 0) + vote.deposit

        # Reward node for correct vote.
        # self.network.reward_node(vote.validator)

        # Enough votes have been received.
        if (self.block_vote_count[vote.source][vote.target] > (self.network.total_deposit * 2) // 3):
            
            # Justify target
            self.justified_checkpoints.add(vote.target)

            # Update highest justified checkpoint.
            if vote.target_height > self.highest_justified_checkpoint.checkpoint_height:
                self.highest_justified_checkpoint = self.received[vote.target]

            # Finalise source if parent of target.
            if vote.source_height == vote.target_height - 1:
                self.network.reward_node(vote.validator)
                self.finalised_checkpoints.add(vote.source)

        return True

    
    def deliver(self, message):
        '''
        Function delivers a message from the network to 
        the validator.
        '''

        # Ignore duplicates.
        if message.hash in self.received:
            return False

        if isinstance(message, Block):
            accepted = self.accept_block(message)
        elif isinstance(message, VoteMessage):
            accepted = self.check_vote(message)

        if accepted:
            
            # Mark as processed.
            self.received[message.hash] = message
            
            # Check message buffer.
            if message.hash in self.message_buffer:
                for d in self.message_buffer[message.hash]:
                    self.deliver(d)
                del self.message_buffer[message.hash]
