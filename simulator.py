"""Simulator function for running the validators and network.
"""

import os
import time

from block import Block
from network import Network
from network import VoteMessage
from votevalidator import VoteValidator
from plot_graph import plot_node_blockchains
from parameters import *


if __name__ == '__main__':
    LOG_DIR = "plot"
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    network = Network(AVG_LATENCY)
    validators = [VoteValidator(network, i) for i in VALIDATOR_IDS]

    num_epochs = 50
    for t in range(BLOCK_PROPOSAL_TIME * CHECKPOINT_DIFF * num_epochs):
        start = time.time()
        network.tick()

        # if t % (BLOCK_PROPOSAL_TIME * CHECKPOINT_DIFF) == 0:
        #     filename = os.path.join(LOG_DIR, "plot_{:03d}.png".format(t))
        #     plot_node_blockchains(validators, filename)
    filename = os.path.join(LOG_DIR, "plot_{:03d}.png".format(t))
    plot_node_blockchains(validators, filename)

    for i in validators:
        print(i.deposit)