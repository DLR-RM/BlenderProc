from src.main.Module import Module

class TrimRedundantChannels(Module):
    """ Removes redundant channels, where the input has more than one channels that share exactly the same value """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image, key, version):
        """
        :param image: The image data.
        :return: The trimmed image data.
        """

        image = image[:, :, 0] # All channles have the same value, so just extract any single channel

        return image, key, version
