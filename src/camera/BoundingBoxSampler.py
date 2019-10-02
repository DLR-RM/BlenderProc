import mathutils
import random


class BoundingBoxSampler(object):

    def __init__(self):
        object.__init__()

    @staticmethod
    def sample(min, max, position_ranges):
        """ Samples a random position inside a bounding box

        :param min: minimum point of the bounding box
        :param max: maximum point of the bounding box
        :param position_ranges: ranges to sample on
        :return:
        """
        position = mathutils.Vector()
        for i in range(3):
            # Check if a interval for sampling has been configured, otherwise sample inside bbox
            if len(position_ranges[i]) != 2:
                position[i] = random.uniform(min[i], max[i])
            else:
                position[i] = random.uniform(min[i] + position_ranges[i][0], min[i] + position_ranges[i][1])

        return position
    