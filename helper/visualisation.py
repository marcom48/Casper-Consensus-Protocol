'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063

Helper functions to draw blockchains.
'''

import random
import matplotlib.pyplot as plt
import networkx as nx
import pygraphviz  # used in the layout

from casper.block import Block
from helper.parameters import *


def create_blockchain(node):

    blockchain = nx.DiGraph()

    # Look at received blocks.
    for block_hash in node.received:

        if isinstance(node.received[block_hash], Block):
            
            block = node.received[block_hash]
            
            # Assert block is a checkpoint.
            if block.is_checkpoint:

                blockchain.add_node(block_hash)

                # Assert not genesis
                if block.height > 0:

                    prev_checkpoint = node.get_checkpoint_parent(block)
                    prev_checkpoint_hash = prev_checkpoint.hash

                    # Add edge from parent.
                    blockchain.add_edge(block_hash, prev_checkpoint_hash)

    return blockchain


def plot_node_blockchains(validators, image_file):

    num_validators = len(validators)

    blockchains = [create_blockchain(i) for i in validators]

    # Set figure size.
    plt.figure(figsize=(40, 20))

    count = 0
    for validator, blockchain in zip(validators, blockchains):
 
        # Create list of committable validators
        colour_list = []

        pos = {}
        labels = {}
        for block_hash in list(blockchain.nodes()):
            block = validator.received[block_hash]

            if validator.is_finalised(block_hash):
                color = '#00B300'
            else:
                color = '#FFA500'
            colour_list.append(color)

            # Randomly distribute children across their height.
            pos[block_hash] = (random.gauss(0, 1), block.checkpoint_height)

        # Create subplot
        ax = plt.subplot(1, len(blockchains), count + 1)
        ax.set_title(f"Validator {validator.id}", fontsize=30)


        # Create graph.
        pos = nx.drawing.nx_agraph.pygraphviz_layout(blockchain, prog='dot')
        
        # Draw.
        nx.draw(blockchain, arrows=True, pos=pos, node_color=colour_list, labels=labels, width = 1, style='dashed', node_shape='s')

        count += 1

    plt.savefig(image_file)
    plt.close()
