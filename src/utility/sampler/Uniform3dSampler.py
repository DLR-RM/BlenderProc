import mathutils
import random


class Uniform3dSampler:
    """ Uniformly samples a 3-dimensional value.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "min", "A list of three values, describing the minimum values for 1st, 2nd, and 3rd dimensions."
       "max", "A list of three values, describing the maximum values for 1st, 2nd, and 3rd dimensions."

    """

    @staticmethod
    def sample(config):
        """
        :param config: A configuration object containing the parameters necessary to sample.
        :return: Sampled value. Type: Mathutils Vector
        """
        # minimum values vector
        min = config.get_vector3d("min")
        # maximum values vector
        max = config.get_vector3d("max")

        position = mathutils.Vector()
        for i in range(3):
            position[i] = random.uniform(min[i], max[i])

        return position
