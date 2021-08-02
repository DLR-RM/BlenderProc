
from src.main.Module import Module
from src.utility.PostProcessingUtility import PostProcessingUtility

class LensDistortion(Module):
    """ TODO """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image, key, version):
        """
        :param image: The image data.
        :return: The lens distorted image data.
        """
        return PostProcessingUtility.apply_lens_distortion(image), key, version
