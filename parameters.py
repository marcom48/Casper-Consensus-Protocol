"""List of parameters for the simulation.
"""

NUM_VALIDATORS = 20  # number of validators at each checkpoint
VALIDATOR_IDS = list(range(0, NUM_VALIDATORS))  # set of validators
BLOCK_PROPOSAL_TIME = 20  # adds a block every 100 ticks
CHECKPOINT_DIFF = 5  # checkpoint every 5 blocks
AVG_LATENCY = 10  # will be modified in metrics
INITIAL_DEPOSIT = 100
BYZANTINE = True
SLASH  = 0.01
REWARD = 0.05
FRAC_BYZ = 3
SAMPLE_SIZE = 10