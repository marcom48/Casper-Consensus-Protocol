
from block import Block, Dynasty
from message import VoteMessage
from parameters import *
from validator import ROOT, Validator
import random


class VoteValidator(Validator):
    """Add the vote messages + slashing conditions capability"""

    def __init__(self, network, id):

        super(VoteValidator, self).__init__(network, id)

        # the head is the latest block processed descendant of the highest
        # justified checkpoint
        self.head = ROOT

        self.deposit = INITIAL_DEPOSIT

        self.highest_justified_checkpoint = ROOT

        self.main_chain_size = 1

        self.proposed_votes = []

        # Set of justified block hashes
        self.justified = {ROOT.hash}

        # Set of finalised block hashes
        self.finalised = {ROOT.hash}

        # Map {validator -> votes}
        # Contains all the votes, and allow us to see who voted for whom
        # Used to check for the slashing conditions
        self.votes = {}

        # Map {source_hash -> {target_hash -> count}} to count the votes
        # ex: self.vote_count[source][target] will be between 0 and NUM_VALIDATORS
        self.vote_count = {}

    # TODO: we could write function is_justified only based on self.processed and self.votes
    #       (note that the votes are also stored in self.processed)

    def is_justified(self, _hash):
        return (_hash in self.justified) and (_hash in self.processed) and (self.processed[_hash].is_checkpoint)

    def is_finalised(self, _hash):
        return (_hash in self.finalised) and (_hash in self.processed) and (self.processed[_hash].is_checkpoint)

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, value):
        self._head = value

    def accept_block(self, block):
        """Called on receiving a block

        Args:
            block: block processed

        Returns:
            True if block was accepted or False if we are missing dependencies
        """
        # If we didn't receive the block's parent yet, wait
        if block.parent_hash not in self.processed:
            self.add_dependency(block.parent_hash, block)
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
        descendants = list(self.tails.items()).copy()
        filter(lambda a: self.is_ancestor(
            self.highest_justified_checkpoint, a[0]), descendants)

        # Sort tails by ascending height.
        descendants.sort(key=lambda a: -a[1].height)

        # Update height
        # TODO: DOES THERE NEED TO BE AN IF?
        if descendants[0][1].height > max_height:
            self.main_chain_size = descendants[0][1].height
            self.head = self.processed[descendants[0][0]]

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
            # assert target_block.checkpoint_height > source_block.checkpoint_height, ("target epoch: {},"
            #                                                                          "source epoch: {}".format(target_block.checkpoint_height, source_block.checkpoint_height))

            # print('Validator %d: now in epoch %d' % (self.id, target_block.checkpoint_height))
            # Increment our epoch
            self.current_height = target_block.checkpoint_height

            # if the target_block is a descendent of the source_block, send
            # a vote
            if self.is_ancestor(source_block, target_block):
                # print('Validator %d: Voting %d for epoch %d with epoch source %d' %
                # (self.id, target_block.hash, target_block.checkpoint_height,
                # source_block.checkpoint_height))

                if random.randint(1, 10) > 11 and len(self.proposed_votes) > 0:

                    print(f"Sent BYZANTINE {self.proposed_votes[0]} ")
                    self.proposed_votes.append(self.proposed_votes[0])
                    self.network.broadcast(self.proposed_votes[0])
                    assert self.processed[target_block.hash]

                else:
                    vote = VoteMessage(source_block.hash,
                                       target_block.hash,
                                       source_block.checkpoint_height,
                                       target_block.checkpoint_height,
                                       self.id, self.deposit)

                    print(f"Sent {vote} ")
                    self.proposed_votes.append(vote)
                    self.network.broadcast(vote)
                    assert self.processed[target_block.hash]

    def accept_vote(self, vote):
        """Called on receiving a vote message.
        """
        # print('Node %d: got a vote' % self.id, source.view, prepare.view_source,
        # prepare.blockhash, vote.blockhash in self.processed)

        # Validator hasn't seen block yet. Add to queue
        if not self.processed.get(vote.source):
            self.add_dependency(vote.source, vote)

        # Check that the source is processed and justified
        # TODO: If the source is not justified, add to dependencies?

        if vote.source not in self.justified:
            print("Not in justified")
            return False

        # If the target has not yet been processed, wait
        if vote.target not in self.processed:
            print("Not in processed")
            self.add_dependency(vote.target, vote)
            return False

        # If the target is not a descendent of the source, ignore the vote
        if not self.is_ancestor(vote.source, vote.target):
            print("Isn't an ancestor")
            return False

        # If the validator is not in the block's dynasty, ignore the vote
        # TODO: is it really vote.target? (to check dynasties)
        # TODO: reorganize dynasties like the paper

        # TODO: Add in function to check if in dynasties
        if vote.validator not in self.processed[vote.target].current_dynasty.validators and \
                vote.validator not in self.processed[vote.target].prev_dynasty.validators:
            print("Not in validator")
            return False

        # Initialize self.votes[vote.validator] if necessary
        if vote.validator not in self.votes:
            self.votes[vote.validator] = []

        # Check the slashing conditions
        # print("-"*20, self.id)
        # print(vote)
        # print("-"*20)
        for past_vote in self.votes[vote.validator]:
            if past_vote.target_height == vote.target_height:
                # TODO: SLASH
                print('You just got slashed.')
                return False

            if ((past_vote.source_height < vote.source_height and
                 past_vote.target_height > vote.target_height) or
                (past_vote.source_height > vote.source_height and
                 past_vote.target_height < vote.target_height)):
                print('You just got slashed.')
                return False

        print("-"*20)

        # Add the vote to the map of votes
        # Successfully passed checks
        self.votes[vote.validator].append(vote)

        # Add to the vote count
        if vote.source not in self.vote_count:
            self.vote_count[vote.source] = {}

        # Otherwise, increase vote

        self.vote_count[vote.source][vote.target] = self.vote_count[
            vote.source].get(vote.target, 0) + vote.deposit

        # TODO: we do not deal with finalised dynasties (the pool of validator
        # is always the same right now)
        # If there are enough votes, process them
        if (self.vote_count[vote.source][vote.target] > (INITIAL_DEPOSIT * NUM_VALIDATORS * 2) // 3):
            # Mark the target as justified
            self.justified.add(vote.target)
            if vote.target_height > self.highest_justified_checkpoint.checkpoint_height:
                self.highest_justified_checkpoint = self.processed[vote.target]

            # If the source was a direct parent of the target, the source
            # is finalised
            if vote.source_height == vote.target_height - 1:
                self.finalised.add(vote.source)
        return True

    # Called on processing any object
    def on_receive(self, obj):
        if obj.hash in self.processed:
            # return False
            # if isinstance(obj, VoteMessage):
            #     print("ALREADY RECV")
            return

        if isinstance(obj, Block):
            result = self.accept_block(obj)
        elif isinstance(obj, VoteMessage):
            print(f"Received {obj} at {self.id}")
            result = self.accept_vote(obj)
        # If the object was successfully processed
        # (ie. not flagged as having unsatisfied dependencies)
        if result:
            self.processed[obj.hash] = obj
            if obj.hash in self.dependencies:
                for d in self.dependencies[obj.hash]:
                    self.on_receive(d)
                del self.dependencies[obj.hash]
