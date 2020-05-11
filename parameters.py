"""List of parameters for the simulation.
"""

NUM_VALIDATORS = 10  # number of validators at each checkpoint
VALIDATOR_IDS = list(range(0, NUM_VALIDATORS))  # set of validators
BLOCK_PROPOSAL_TIME = 10  # adds a block every 100 ticks
CHECKPOINT_DIFF = 5  # checkpoint every 5 blocks
AVG_LATENCY = 100  # will be modified in metrics
INITIAL_DEPOSIT = 100
BYZANTINE = True