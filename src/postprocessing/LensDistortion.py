from src.main.Module import Module
from src.utility.PostProcessingUtility import PostProcessingUtility


class LensDistortion(Module):
    """ This module can be used to postprocess images to apply a certain lens distortion, we rely here on the values:

            k1, k2, k3 and p1, p2

        Here k_n is the radial distortion coefficient defined by the Brown-Conrady model and
        p_n is the tangential distortion coefficient.

        For more information on this see: https://en.wikipedia.org/wiki/Distortion_(optics)
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image, key, version):
        """
        :param image: The image data.
        :return: The lens distorted image data.
        """
        return PostProcessingUtility.apply_lens_distortion(image), key, version
