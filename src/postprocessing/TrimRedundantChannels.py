import numpy as np

from src.main.Module import Module

class TrimRedundantChannels(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, data):

        data = data[:,:,0]

        return data
