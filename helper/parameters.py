'''
COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063
'''

########## Execution Parameters ##########

VALIDATORS = 5

# How often to propose a block.
BLOCK_FREQUENCY = 10

# Height difference between checkpoints
CHECKPOINT_DIFF = 5

# Number of checkpoints.
CHECKPOINTS = 50

# Average network latency.
AVG_LATENCY = 10

# Initial deposit for validators.
INITIAL_DEPOSIT = 100

# Percentage values to slash/reward validators.
SLASH  = 0.01
REWARD = 0.05


########## Simulation Parameters ##########

# Directory to draw simulation blockchains.
SIMULATION_FOLDER = 'simulation_blockchains'

# Directory to draw fault tolerance graphs.
FAULT_FOLDER = 'fault_graphs'


# Sample size for fault testing.
SAMPLE_SIZE = 10

# Plot simulations blockchains progressively.
PROGRESSIVE_PLOT = False

# Fraction of simulation validators that are Byzantine.
FRAC_BYZ = 0