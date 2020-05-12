
from block import Block
from network import VoteMessage
from parameters import *
from validator import ROOT, Validator
import random
from utils import generate_hash
import math

class VoteValidator(Validator):


    def __init__(self, network, id):
        super(VoteValidator, self).__init__(network, id)

        self.head = ROOT

        self.deposit = INITIAL_DEPOSIT

        self.highest_justified_checkpoint = ROOT

        self.main_chain_size = 1


        # Justified checkpoints.
        self.justified_checkpoints = {ROOT.hash}

        # Finalised checkpoints
        self.finalised_checkpoints = {ROOT.hash}

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

        # Haven't recieved block's parent.
        if block.parent_hash not in self.received:
            self.add_message_buffer(block.parent_hash, block)
            return False

        
        self.received[block.hash] = block

        if block.is_checkpoint:

            #  Start a tail object for it
            self.path_membership[block.hash] = block.hash
            self.paths[block.hash] = block

            # Maybe vote
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

        if self.is_ancestor(self.highest_justified_checkpoint, self.path_membership[block.hash]):
            
            # Update current working head.
            self.head = block
            self.main_chain_size += 1

        else:
            
            # Change path to find current highest head.
            self.fix_head(block)

        return True

    # Adjust current head to highest checkpointed head 
    def fix_head(self, block):

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

        # assert block.height % CHECKPOINT_DIFF == 0, (
        #     "Block {} is not a checkpoint.".format(block.hash))

        # Create blocks for supermajority link vote.
        target_block = block
        source_block = self.highest_justified_checkpoint

        # Assert creating a block for a new height.
        if target_block.checkpoint_height > self.current_height:

            # assert target_block.checkpoint_height > source_block.checkpoint_height, ("target epoch: {},"
            # "source epoch: {}".format(target_block.checkpoint_height, source_block.checkpoint_height))

            # Adjust current working height.
            self.current_height = target_block.checkpoint_height

            if self.is_ancestor(source_block, target_block):
                

                # if random.randint(0,50) > 40 and BYZANTINE and len(self.proposed_votes) > 0:
                if self.id < math.ceil(NUM_VALIDATORS/FRAC_BYZ) and BYZANTINE and len(self.proposed_votes) > 0:

                    n = len(self.proposed_votes)

                    # Submit random previous vote to violate slashing condition 1.
                    vote = self.proposed_votes[random.randint(0, n-1)]

                    # Update hash so doesn't appear as duplicate.
                    vote.hash = generate_hash()

                                
                else:
                    vote = VoteMessage(source_block.hash,
                                target_block.hash,
                                source_block.checkpoint_height,
                                target_block.checkpoint_height,
                                self.id, self.deposit)

                self.proposed_votes.append(vote)
                #print(f"Validator {self.id} voting for block {target_block.hash}")
                self.network.broadcast(vote, self.id)
                self.deliver(vote)
                

                assert self.received[target_block.hash]


    def slashing_conditions(self, new_vote):
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

        # Enough votes have been received.
        if (self.block_vote_count[vote.source][vote.target] > (self.network.total_deposit * 2) // 3):
            
            # Justify target
            #print(f"Validator {self.id} justifying block {vote.target}")
            self.justified_checkpoints.add(vote.target)

            # Update highest justified checkpoint.
            if vote.target_height > self.highest_justified_checkpoint.checkpoint_height:
                self.highest_justified_checkpoint = self.received[vote.target]

            # Finalise source if parent of target.
            if vote.source_height == vote.target_height - 1:
                #print(f"Validator {self.id} finalising block {vote.source}")

                self.network.reward_node(self.id)
                self.finalised_checkpoints.add(vote.source)

        return True

    
    def deliver(self, message):

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
