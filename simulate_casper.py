'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063
'''

import os, math
from casper.network import Network
from casper.caspervalidator import CasperValidator
from helper.visualisation import plot_node_blockchains
from helper.parameters import *



def main():
    '''
    Function simulates blockchain environment with parameters
    set in parameters.py, creates a greaph of chains generated
    in /SIMULATION_FOLDER.
    '''    
    
    if not os.path.exists(SIMULATION_FOLDER):
        os.makedirs(SIMULATION_FOLDER)

    # Create simulated network.
    network = Network(AVG_LATENCY)

    # Create simulated validators.
    validators = [CasperValidator(network, i) for i in list(range(VALIDATORS))]


    if FRAC_BYZ != 0:
        for j in range(math.ceil(VALIDATORS/FRAC_BYZ)):
            validators[j].byzantine = True


    # Run simulation
    for time in range(BLOCK_FREQUENCY * CHECKPOINT_DIFF * CHECKPOINTS):

        network.execute()

        # New checkpoint.
        if PROGRESSIVE_PLOT and  (not (time % (BLOCK_FREQUENCY * CHECKPOINT_DIFF)) ):
            
            # Create filename with logical time value.
            filename = os.path.join(SIMULATION_FOLDER, f"blockchain_{time}.png")
            
            plot_node_blockchains(validators, filename)

    # Save final blockchain.
    filename = os.path.join(SIMULATION_FOLDER, f"blockchain_{time}.png")    
    plot_node_blockchains(validators, filename)


if __name__ == '__main__':
    main()
    