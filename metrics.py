import os
import sys
import numpy as np

from parameters import *
from block import Block
from network import Network
from votevalidator import VoteValidator
from plot_graph import plot_node_blockchains
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns



def fraction_justified_and_finalised(validator):
    """Compute the fraction of justified and finalised checkpoints in the main chain.

    From the genesis block to the highest justified checkpoint, count the fraction of checkpoints
    in each state.
    """
    # Get the main chain
    checkpoint = validator.highest_justified_checkpoint

    count_justified = 0
    count_finalised = 0
    count_total = 0
    while checkpoint is not None:
        count_total += 1
        if checkpoint.hash in validator.justified_checkpoints:
            count_justified += 1
        if checkpoint.hash in validator.finalised_checkpoints:
            count_finalised += 1
        checkpoint = validator.get_checkpoint_parent(checkpoint)

    fraction_justified = float(count_justified) / float(count_total)
    fraction_finalised = float(count_finalised) / float(count_total)
    count_forked_justified = len(validator.justified_checkpoints) - count_justified
    fraction_forked_justified = float(count_forked_justified) / float(count_total)
    return fraction_justified, fraction_finalised, fraction_forked_justified


def main_chain_size(validator):
    """Computes the number of blocks in the main chain."""
    return validator.highest_justified_checkpoint.height + 1


def blocks_under_highest_justified(validator):
    """Computes the height of blocks below the checkpoint of highest height."""
    res = 0
    for bhash, b in validator.received.items():
        if isinstance(b, Block):
            if b.height <= validator.highest_justified_checkpoint.height:
                res += 1
    return res


def total_height_blocks(validator):
    """Total height of blocks processed by the validator.
    """
    res = 0
    for bhash, b in validator.received.items():
        if isinstance(b, Block):
            res += 1
    return res


def count_forks(validator):
    """Compute the height of forks of each size.

    Returns a dict {1: 24, 2: 5, 3: 2} for instance.
    Compute forks up until the highest justified checkpoint.
    """
    # Compute a list of the block hashes in the main chain, up to the highest justified checkpoint.
    block = validator.highest_justified_checkpoint
    block_hash = block.hash
    main_blocks = [block_hash]

    # Stop when we reach the genesis block
    while block.height > 0:
        block_hash = block.prevhash
        block = validator.received[block_hash]
        main_blocks.append(block_hash)

    # Check that we reached the genesis block
    assert block.height == 0
    assert len(main_blocks) == validator.highest_justified_checkpoint.height + 1

    # Now iterate through the blocks with height below highest_justified
    longest_fork = {}
    for block_hash, block in validator.received.items():
        if isinstance(block, Block):
            if block.height <= validator.highest_justified_checkpoint.height:
                # Get the closest parent of block from the main blockchain
                fork_length = 0
                while block_hash not in main_blocks:
                    fork_length += 1
                    block_hash = block.prevhash
                    block = validator.received[block_hash]
                assert block_hash in main_blocks
                longest_fork[block_hash] = max(longest_fork.get(block_hash, 0), fork_length)

    count_forks = {}
    for block_hash in main_blocks:
        l = longest_fork[block_hash]
        count_forks[l] = count_forks.get(l, 0) + 1

    assert sum(count_forks.values()) == validator.highest_justified_checkpoint.height + 1
    return count_forks


def print_metrics_latency(latencies, SAMPLE_SIZE, validator_set=VALIDATOR_IDS):

    results = {}

    for latency in latencies:
        jfsum = 0.0
        ffsum = 0.0
        jffsum = 0.0
        mcsum = 0.0
        busum = 0.0
        #fcsum = {}
        for i in range(SAMPLE_SIZE):
            network = Network(latency)
            validators = [VoteValidator(network, i) for i in validator_set]

            for t in range(BLOCK_PROPOSAL_TIME * CHECKPOINT_DIFF * 50):
                network.tick()
                # if t % (BLOCK_PROPOSAL_TIME * CHECKPOINT_DIFF) == 0:
                #     filename = os.path.join(LOG_DIR, 'plot_{:03d}.png'.format(t))
                #     plot_node_blockchains(validators, filename)

            for val in validators:
                jf, ff, jff = fraction_justified_and_finalised(val)
                jfsum += jf
                ffsum += ff
                jffsum += jff
                mcsum += main_chain_size(val)
                busum += blocks_under_highest_justified(val)
                #fc = count_forks(val)
                #for l in fc.keys():
                    #fcsum[l] = fcsum.get(l, 0) + fc[l]

        print('Latency: {}'.format(latency))
        print('Justified: {}'.format(jfsum / len(validators) / SAMPLE_SIZE))
        print('finalised: {}'.format(ffsum / len(validators) / SAMPLE_SIZE))
        print('Justified in forks: {}'.format(jffsum / len(validators) / SAMPLE_SIZE))
        print('Main chain size: {}'.format(mcsum / len(validators) / SAMPLE_SIZE))
        print('Blocks under main justified: {}'.format(busum / len(validators) / SAMPLE_SIZE))
        print('Main chain fraction: {}'.format(
            mcsum / (len(validators) * SAMPLE_SIZE * (CHECKPOINT_DIFF * 50 + 1))))

        results[latency] = {}
        results[latency]['justified'] = jfsum / len(validators) / SAMPLE_SIZE
        results[latency]['finalised'] = ffsum / len(validators) / SAMPLE_SIZE
        # results[latency]['Justified in forks'] = jffsum / len(validators) / SAMPLE_SIZE
        # results[latency]['Main chain size'] = mcsum / len(validators) / SAMPLE_SIZE
        # results[latency]['Blocks under main justified'] = busum / len(validators) / SAMPLE_SIZE

        results[latency]['Main chain fraction'] = mcsum / (len(validators) * SAMPLE_SIZE * (CHECKPOINT_DIFF * 50 + 1))

        #for l in sorted(fcsum.keys()):
            #if l > 0:
                #frac = float(fcsum[l]) / float(fcsum[0])
                #print('Fraction of forks of size {}: {}'.format(l, frac))
        print('')

    return results


def plot_line_graphs(df, title, xlabel, ylabel, filename):
    sns.set_style("darkgrid")
    plot = sns.lineplot(data=df, size=15)

    fig, ax = plt.subplots(figsize=(10,10))
    sns.lineplot(ax=ax, data=df, markers=True)
    plt.xlabel(xlabel, fontsize=15)
    plt.ylabel(ylabel, fontsize=15)
    plt.title(title, fontsize=25)
    plt.ylim(0,1)
    fig.savefig(f"{filename}.png")



def latency_test():
    SAMPLE_SIZE = 10
    latencies = [i for i in range(25)]
    # latencies = [5,10,15,20]
    num_validators = NUM_VALIDATORS
    validator_set = VALIDATOR_IDS
    results = print_metrics_latency(latencies, SAMPLE_SIZE, validator_set)

    for i in latencies:
        results[i]['Theoretical'] = 1 - (i/(i + BLOCK_PROPOSAL_TIME))

    df = pd.DataFrame(results)
    df = df.transpose()
    plot_line_graphs(df, "Latency Impact on Casper", "Average Latency", "Percentage",  "LatencyImpact")


def partition_test():
    SAMPLE_SIZE = 10
    latencies = [AVG_LATENCY]
    fractions = [0.05, 0.1, 0.2, 0.3, 0.33, 0.34, 0.4]
    results = {}
    for frac in fractions:

        num_validators = int((1.0 - frac) * NUM_VALIDATORS)
        validator_set = VALIDATOR_IDS[:num_validators]
        print(f"Fraction disconnected {frac}")
        results[frac] = print_metrics_latency(latencies, SAMPLE_SIZE, validator_set)

    dfs = []
    for i in results:
        temp = pd.DataFrame(results[i])
        temp = temp.transpose()
        temp.index = [i]
        dfs.append(temp)

    results = pd.concat(dfs)
    plot_line_graphs(results, "Partition Impact on Casper", "Network Partition", "Percentage", "PartitionImpact")
    
def byzantine_test():
    SAMPLE_SIZE = 10
    latencies = [AVG_LATENCY]
    fractions = [10,9,8,7,6,6,5,4,3,2]
    results = {}
    for frac in fractions:

        num_validators = NUM_VALIDATORS
        validator_set = VALIDATOR_IDS
        FRAC_BYZ = frac

        print(f"Fraction Byzantine 1/{frac}")
        results[frac] = print_metrics_latency(latencies, SAMPLE_SIZE, validator_set)

    dfs = []
    for i in results:
        temp = pd.DataFrame(results[i])
        temp = temp.transpose()
        temp.index = [i]
        dfs.append(temp)

    results = pd.concat(dfs)
    plot_line_graphs(results, "Byzantine Impact on Casper", "Byzantine Fraction", "Percentage", "ByzantineImpact")
    

if __name__ == '__main__':
    LOG_DIR = 'metrics'
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)



    try:

        if sys.argv[1] not in ['latency', 'network', 'byzantine']:
            print("Wrong test configuration.")
            sys.exit()

    except:
        print("Wrong test configuration.")
        sys.exit()

    test_type = sys.argv[1]
    
    SAMPLE_SIZE = 10

    print(f"Performing {test_type} simulation...")

    if test_type == 'latency':
        # latencies = [1] + [i for i in range(2,42,2)]
        latency_test()

    elif test_type == 'network':
        
        partition_test()


    else:
        byzantine_test()

