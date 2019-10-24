import mathutils
import random


class BoundingBoxSampler:
    """ Samples a random position inside a bounding box

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "min", "A list of three values, describing the x, y and z coordinate of the minimum point of the bounding box."
       "max", "A list of three values, describing the x, y and z coordinate of the maximum point of the bounding box."

    """

    @staticmethod
    def sample(config):
        """
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