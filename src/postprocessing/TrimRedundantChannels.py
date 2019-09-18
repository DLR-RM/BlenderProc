import numpy as np

from src.main.Module import Module

class TrimRedundantChannels(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, data):
        """ Removes redundant channels, where the input has more than one channels that share exactly the same value
        
        :param data: The image data.
        :return: The trimmed image data.
        """

        data = data[:,:,0] # All channles have the same value, so just extract any single channel

        return data
