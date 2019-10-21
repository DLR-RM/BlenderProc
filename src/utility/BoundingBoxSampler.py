import mathutils
import random


class BoundingBoxSampler(object):

    def __init__(self):
        object.__init__()

    @staticmethod
    def sample(config):
        """ Samples a random position inside a bounding box

        :param config: A configuration object containing the parameters necessary to sample.
        :return: position vector of the sampled point Type: Mathutils Vector
        """
        # minimum point of the bounding box
        min = config.get_vector3d("min")
        # maximum point of the bounding box
        max = config.get_vector3d("max")

        position = mathutils.Vector()
        for i in range(3):
            position[i] = random.uniform(min[i], max[i])

        return position