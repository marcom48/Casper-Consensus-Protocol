'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063
'''

import math, os, sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from casper.block import Block
from helper.parameters import *
from casper.network import Network
from casper.caspervalidator import CasperValidator
from helper.visualisation import plot_node_blockchains


def frac_just_fin(validator):
    
    '''
    Method computes the fraction of nodes in the main chain
    that are finalised or justified for a validator.
    '''

    # Start at highest checkpoint
    curr_block = validator.highest_justified_checkpoint

    justified = 0

    finalised = 0
    
    total = 0

    # Traverse blockchain.
    while curr_block is not None:
        
        total += 1
        
        if curr_block.hash in validator.justified_checkpoints:
            justified += 1
        
        if curr_block.hash in validator.finalised_checkpoints:
            finalised += 1
        
        curr_block = validator.get_checkpoint_parent(curr_block)


    frac_justified = float(justified) / float(total)
    frac_finalised = float(finalised) / float(total)
    
    
    return frac_justified, frac_finalised


def below_highest_checkpoint(validator):
    '''
    Method computes the height of blocks below highest checkpoint.
    '''

    val = 0
    for block in validator.received.values():

        if isinstance(block, Block) and block.height <= validator.highest_justified_checkpoint.height:
            val += 1

    return val


def run_tests(latencies, frac_byz, validator_set):
    '''
    Function runs tests on network for various input
    parameters.
    '''

    results = {}

    for latency in latencies:

        # Initialise variables.
        total_justified = 0.0
        total_finalised = 0.0
        jtotal_finalised = 0.0
        total_main_chain = 0.0
        total_under_main = 0.0

        # Perform tests.
        for i in range(SAMPLE_SIZE):
            
            # Create network and validators.
            network = Network(latency)
            validators = [CasperValidator(network, i) for i in validator_set]

            # Convert to Byzantine.
            if frac_byz != 0:
                for j in range(math.ceil(VALIDATORS/frac_byz)):
                    validators[j].byzantine = True

            # Run execution.
            for _ in range(BLOCK_FREQUENCY * CHECKPOINT_DIFF * CHECKPOINTS):
                network.execute()

            # Gather results.
            for validator in validators:

                justified_frac, finalised_frac = frac_just_fin(validator)
                total_justified += justified_frac
                total_finalised += finalised_frac

                total_main_chain += validator.highest_justified_checkpoint.height + 1
                total_under_main += below_highest_checkpoint(validator)

        # Compute averages.
        average_justified = total_justified / len(validators) / SAMPLE_SIZE
        average_finalised = total_finalised / len(validators) / SAMPLE_SIZE
        average_mainchain = total_main_chain / len(validators) / SAMPLE_SIZE
        average_frac_of_main = total_main_chain / (len(validators) * SAMPLE_SIZE * (CHECKPOINT_DIFF * CHECKPOINTS + 1))

        print(f'Average Latency: {latency}')
        print(f'Average number justified: {average_justified}')
        print(f'Average number finalised: {average_finalised}')
        print(f'Average main chain size: {average_mainchain}')
        print(f'Average fraction of blocks in main chain: {average_frac_of_main}')

        # Add results to dictionary.
        results[latency] = {}
        results[latency]['justified'] = average_justified
        results[latency]['finalised'] = average_finalised
        results[latency]['Main chain fraction'] = average_frac_of_main
        
        print()

    return results


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


def collate_results(results):
    dfs = []
    for i in results:
        temp = pd.DataFrame(results[i])
        temp = temp.transpose()
        temp.index = [i]
        dfs.append(temp)

    df = pd.concat(dfs)
    return df


def latency_test():
    '''
    Function performs test over differing average
    network latency values.
    '''
        
    latencies = [i for i in range(25)]
    
    num_validators = VALIDATORS
    
    validator_set = list(range(VALIDATORS))
    
    results = run_tests(latencies, 0, validator_set)

    # Add in theoretical results.
    for i in latencies:
        results[i]['Theoretical'] = 1 - (i/(i + BLOCK_FREQUENCY))

    df = pd.DataFrame(results)
    df = df.transpose()

    # Plot results.
    plot_line_graphs(df, "Latency Impact on Casper", "Average Latency", "Percentage",  "LatencyImpact")


def partition_test():
    '''
    Function performs test over differing
    network partition sizes.
    '''

    latencies = [AVG_LATENCY]
    fractions = [0.05, 0.1, 0.2, 0.3, 0.33, 0.34, 0.4]
    results = {}
    for frac in fractions:

        print(f"Fraction disconnected {frac}")
        
        # Create a subset of the total number of validators.
        num_validators = int((1.0 - frac) * VALIDATORS)
        validator_set = list(range(VALIDATORS))[:num_validators]
        
        results[frac] = run_tests(latencies, 0, validator_set)


    # Plot results.
    plot_line_graphs(collate_results(results), "Partition Impact on Casper", "Network Partition", "Percentage", "PartitionImpact")
    
def byzantine_test():
    '''
    Function performs test over differing fractions
    of Byzantine validators.
    '''

    SAMPLE_SIZE = 10
    latencies = [AVG_LATENCY]
    fractions = [10,9,8,7,6,6,5,4,3,2]

    results = {}
    
    for frac in fractions:

        num_validators = VALIDATORS
        validator_set = list(range(VALIDATORS))
        FRAC_BYZ = frac

        print(f"Fraction Byzantine 1/{frac}")
        results[frac] = run_tests(latencies, frac, validator_set)

    # Plot results.
    plot_line_graphs(collate_results(results), "Byzantine Impact on Casper", "Byzantine Fraction", "Percentage", "ByzantineImpact")
    


def main():

    try:

        if sys.argv[1] not in ['latency', 'network', 'byzantine']:
            print("Wrong test configuration.")
            sys.exit()

    except:
        print("Wrong test configuration.")
        sys.exit()


    if not os.path.exists(FAULT_FOLDER):
        os.makedirs(FAULT_FOLDER)

    test_type = sys.argv[1]
    print(f"Performing {test_type} simulation...")

    if test_type == 'latency':

        latency_test()

    elif test_type == 'network':
        
        partition_test()
    
    else:
        byzantine_test()



if __name__ == '__main__':
    main()

