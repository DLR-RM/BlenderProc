import mathutils
import random


class BoundingBoxSampler(object):

    def __init__(self):
        object.__init__()

    @staticmethod
    def sample(min, max):
        """ Samples a random position inside a bounding box

        :param min: minimum point of the bounding box. Type: Mathutils Vector
        :param max: maximum point of the bounding box Type: Mathutils Vector
        :return: position vector of the sampled point Type: Mathutils Vector
        """
        position = mathutils.Vector()
        for i in range(3):
            position[i] = random.uniform(min[i], max[i])

        return position
    