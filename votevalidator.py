

from block import Block
from network import VoteMessage
from parameters import *
from validator import ROOT, Validator
import random

class VoteValidator(Validator):
    """Add the vote messages + slashing conditions capability"""

    def __init__(self, network, id):
        super(VoteValidator, self).__init__(network, id)

        self.head = ROOT

        self.deposit = INITIAL_DEPOSIT

        self.highest_justified_checkpoint = ROOT

        self.main_chain_size = 1

        # Votes proposed to network.
        self.proposed_votes = []

        # Set of justified block hashes
        self.justified_checkpoints = {ROOT.hash}

        # Finalised blocks
        self.finalised_checkpoints = {ROOT.hash}

        # Record of previous votes for each validator.
        # Used to test slashing conditions.
        self.votes = {}

        # Record of number of votes for each proposed block.
        self.vote_count = {}
    

    # Check a checkpoitn is justified.
    def is_justified(self, _hash):

        return (_hash in self.justified_checkpoints) and (_hash in self.processed) and (self.processed[_hash].is_checkpoint)

    # Check a checkpoint is finalised
    def is_finalised(self, _hash):
        return (_hash in self.finalised_checkpoints) and (_hash in self.processed) and (self.processed[_hash].is_checkpoint)



    def accept_block(self, block):
        """Called on receiving a block

        Args:
            block: block processed

        Returns:
            True if block was accepted or False if we are missing buffer
        """
        # If we didn't receive the block's parent yet, wait
        if block.parent_hash not in self.processed:
            self.add_to_buffer(block.parent_hash, block)
            return False

        # We receive the block
        self.processed[block.hash] = block

        # If it's an epoch block (in general)
        # If it's a checkpoint
        if block.is_checkpoint:

            #  Start a tail object for it
            self.tail_membership[block.hash] = block.hash
            self.tails[block.hash] = block

            # Maybe vote
            self.maybe_vote_last_checkpoint(block)

        # Otherwise...
        else:
            # See if it's part of the longest tail, if so set the tail accordingly
            assert block.parent_hash in self.tail_membership

            # The new block is in the same tail as its parent
            self.tail_membership[block.hash] = self.tail_membership[block.parent_hash]

            curr_tail = self.tail_membership[block.hash]

            # If the block has the highest height, it becomes the end of the tail
            if block.height > self.tails[curr_tail].height:
                self.tails[curr_tail] = block

        # This block is in the same path as the highest checkpoint
        if self.is_ancestor(self.highest_justified_checkpoint, self.tail_membership[block.hash]):
            self.head = block
            self.main_chain_size += 1
        else:
            # Need to update where the current head is
            self.fix_head(block)

        return True

    def fix_head(self, block):
        """Reorganize the head to stay on the chain with the highest
        justified checkpoint.

        If we are on wrong chain, reset the head to be the highest descendent
        among the chains containing the highest justified checkpoint.

        Args:
            block: latest block processed."""

        # Find the highest descendant of the highest justified checkpoint
        # and set it as head
        # print('Wrong chain, reset the chain to be a descendant of the '
        # 'highest justified checkpoint.')
        max_height = self.highest_justified_checkpoint.height
        max_descendant = self.highest_justified_checkpoint.hash


        # Find all tails that highest checkpoint is ancestor of
        descendants = list(self.tails.keys()).copy()        

        descendants = list(filter(lambda a: self.is_ancestor(
            self.highest_justified_checkpoint, a), descendants))


        # # # Sort tails by ascending height.
        descendants.sort(key=lambda a: -self.processed[a].height)

        highest_desc = max(descendants, key = lambda a: self.processed[a].height)



        # Update height
        # TODO: DOES THERE NEED TO BE AN IF?
        if self.processed[highest_desc].height > max_height:
            self.main_chain_size = self.processed[highest_desc].height
            self.head = self.processed[highest_desc]
        # else:
        #     print("FALSE")

    def maybe_vote_last_checkpoint(self, block):
        """Called after receiving a block.

        Implement the fork rule:
        maybe send a vote message where target is block
        if we are on the chain containing the justified checkpoint of the
        highest height, and we have never sent a vote for this height.

        Args:
            block: last block we processed
        """
        assert block.height % EPOCH_SIZE == 0, (
            "Block {} is not a checkpoint.".format(block.hash))

        # BNO: The target will be block (which is a checkpoint)
        target_block = block
        # BNO: The source will be the justified checkpoint of greatest height
        source_block = self.highest_justified_checkpoint

        # If the block is an epoch block of a higher epoch than what we've seen so far
        # This means that it's the first time we see a checkpoint at this height
        # It also means we never voted for any other checkpoint at this height (rule 1)
        if target_block.checkpoint_height > self.current_height:
            assert target_block.checkpoint_height > source_block.checkpoint_height, ("target epoch: {},"
                                                                                     "source epoch: {}".format(target_block.checkpoint_height, source_block.checkpoint_height))

            # print('Validator %d: now in epoch %d' % (self.id, target_block.checkpoint_height))
            # Increment our epoch
            self.current_height = target_block.checkpoint_height

            
            if self.is_ancestor(source_block, target_block):


                if random.randint(1, 40) > 30 and len(self.proposed_votes) > 0 and BYZANTINE:

                    self.slashed = False
                    self.proposed_votes.append(self.proposed_votes[0])
                    self.network.broadcast(self.proposed_votes[0])
                    assert self.processed[target_block.hash]

                else:
                    vote = VoteMessage(source_block.hash,
                                       target_block.hash,
                                       source_block.checkpoint_height,
                                       target_block.checkpoint_height,
                                       self.id, self.deposit)

                    #print(f"Sent {vote} ")
                    self.proposed_votes.append(vote)
                    self.network.broadcast(vote)
                    assert self.processed[target_block.hash]

    def slashing_conditions(self, new_vote):
        # Check the slashing conditions
        for past_vote in self.votes[new_vote.validator]:

            # No duplicate target heights.
            if past_vote.target_height == new_vote.target_height:

                self.network.slash_node(new_vote.validator)

                return False

            # No voting within previous votes.
            if ((past_vote.source_height < new_vote.source_height and
                 past_vote.target_height > new_vote.target_height) or
               (past_vote.source_height > new_vote.source_height and
                 past_vote.target_height < new_vote.target_height)):


                return False

        return True

    def accept_vote(self, vote):

       # If the block has not yet been processed, wait
        if vote.source not in self.processed:
            self.add_to_buffer(vote.source, vote)

        # Check that the source is justified
        if vote.source not in self.justified_checkpoints :
            return False

        # If the target has not yet been processed, wait
        if vote.target not in self.processed:
            self.add_to_buffer(vote.target, vote)
            return False

        # If the target is not a descendent of the source, ignore the vote
        if not self.is_ancestor(vote.source, vote.target):
            return False

        # Not necessary for static validator set, but present to demonstrate algorithm condition.
        if vote.validator not in self.processed[vote.target].validators:
            return False

        # Create record of validators votes.
        if vote.validator not in self.votes:
            self.votes[vote.validator] = []

        # Check the slashing conditions
        if not self.slashing_conditions(vote):
            return False

        # Add the vote to the map of votes
        self.votes[vote.validator].append(vote)

        # Add to the vote count
        if vote.source not in self.vote_count:
            self.vote_count[vote.source] = {}
        self.vote_count[vote.source][vote.target] = self.vote_count[
            vote.source].get(vote.target, 0) + vote.deposit


        # If there are enough votes, process them
        if (self.vote_count[vote.source][vote.target] > (self.network.total_deposit * 2) // 3):
            # Mark the target as justified
            self.justified_checkpoints.add(vote.target)
            if vote.target_height > self.highest_justified_checkpoint.checkpoint_height:
                self.highest_justified_checkpoint = self.processed[vote.target]

            # If the source was a direct parent of the target, the source
            # is finalised
            if vote.source_height == vote.target_height - 1:

                # Reward node for finalising block.
                self.network.reward_node(id)

                self.finalised_checkpoints.add(vote.source)
        
        return True

    # Called on processing any object
    def deliver(self, obj):

        # Ignore duplicate votes.
        # CAN THIS JUST BE REMOVED
        if not BYZANTINE and obj.hash in self.processed:
            return False

        # Received proposed block.
        if isinstance(obj, Block):
            accepted = self.accept_block(obj)

        # Received vote.
        else:
            accepted = self.accept_vote(obj)
        
        
        if accepted:

            # Record message hash to not process again.
            self.processed[obj.hash] = obj

            # Check if any previous messages required current message.
            if obj.hash in self.buffer:

                for d in self.buffer[obj.hash]:
                    self.deliver(d)

                # Remove previous message.
                del self.buffer[obj.hash]
