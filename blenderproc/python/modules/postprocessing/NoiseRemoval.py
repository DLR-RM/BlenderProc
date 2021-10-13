from blenderproc.python.modules.main.Module import Module
from blenderproc.python.postprocessing.PostProcessingUtility import remove_segmap_noise


class NoiseRemoval(Module):
    """Removes noise pixels.

    Assumes that noise pixel values won't occur more than 100 times.
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image, key, version):
        """
        :param image: The image data.
        :param key: The key to use when writing to the .hdf5.
        :param version: Version of the original data.
        :return: The cleaned image data, key to use when writing and version numer.
        """
        return remove_segmap_noise(image), key, version
