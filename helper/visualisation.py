'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063

Helper functions to plot blockchains and graphs.
'''

import random, os
import matplotlib.pyplot as plt
import networkx as nx
import pygraphviz
import matplotlib.pyplot as plt
import seaborn as sns

from casper.block import Block
from helper.parameters import *


def create_blockchain(node, labels):

    blockchain = nx.DiGraph()

    # Look at received blocks.
    for block_hash in node.received:

        if isinstance(node.received[block_hash], Block):
            
            block = node.received[block_hash]
            
            # Assert block is a checkpoint.
            if block.is_checkpoint:

                blockchain.add_node(block_hash)

                # Create one-to-one mapping of hash to label
                if block_hash not in labels:
                    count = len(labels)
                    labels[block_hash] = count

                # Assert not genesis
                if block.height > 0:

                    prev_checkpoint = node.get_checkpoint_parent(block)
                    prev_checkpoint_hash = prev_checkpoint.hash

                    # Add edge from parent.
                    blockchain.add_edge(block_hash, prev_checkpoint_hash)

    return blockchain


def plot_node_blockchains(validators, image_file):


    labels = {}

    num_validators = len(validators)

    blockchains = [create_blockchain(i, labels) for i in validators]

    # Set figure size.
    plt.figure(figsize=(40, 20))

    count = 0
    for validator, blockchain in zip(validators, blockchains):
 
        # Create list of committable validators
        colour_list = []

        pos = {}
        for block_hash in list(blockchain.nodes()):
            block = validator.received[block_hash]

            if validator.is_finalised(block_hash):
                color = '#00B300'
            elif validator.is_justified(block_hash):
                color = '#FFA500'
            else:
                color = 'r'
            colour_list.append(color)

            # Randomly distribute children across their height.
            pos[block_hash] = (random.gauss(0, 1), block.checkpoint_height)

        # Create subplot
        ax = plt.subplot(1, len(blockchains), count + 1)
        ax.set_title(f"Validator {validator.id + 1}", fontsize=30)


        # Create graph.
        pos = nx.drawing.nx_agraph.pygraphviz_layout(blockchain, prog='dot')
        
        # Draw.
        blockchain = nx.DiGraph.reverse(blockchain)
        nx.draw(blockchain, arrows=True, pos=pos, node_color=colour_list, labels=labels, width = 1, style='dashed', node_shape='s')

        count += 1

    plt.savefig(image_file)
    plt.close()


def plot_line_graphs(df, title, xlabel, ylabel, filename):
    '''
    Function plots results of tests.
    '''
    sns.set_style("darkgrid")
    plot = sns.lineplot(data=df, size=15)

    fig, ax = plt.subplots(figsize=(10,10))
    sns.lineplot(ax=ax, data=df, markers=True)
    plt.xlabel(xlabel, fontsize=15)
    plt.ylabel(ylabel, fontsize=15)
    plt.title(title, fontsize=25)
    plt.ylim(0,1)
    filename = os.path.join(FAULT_FOLDER, f"{filename}.png")   
    fig.savefig(filename)