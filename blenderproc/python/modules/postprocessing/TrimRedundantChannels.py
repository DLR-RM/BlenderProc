from blenderproc.python.modules.main.Module import Module
from blenderproc.python.postprocessing.PostProcessingUtility import trim_redundant_channels

class TrimRedundantChannels(Module):
    """ Removes redundant channels, where the input has more than one channels that share exactly the same value """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image, key, version):
        """
        :param image: The image data.
        :return: The trimmed image data.
        """
        return trim_redundant_channels(image), key, version
