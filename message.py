import random
import utils


class VoteMessage():

    def __init__(self, source, target, source_height, target_height, validator, deposit):
        self.source = source
        self.target = target
        self.source_height = source_height
        self.target_height = target_height
        self.validator = validator
        self.hash = utils.generate_hash()
        self.deposit = deposit

    def __str__(self):
        return f'{self.source_height}, {self.target_height}, {self.validator}'
