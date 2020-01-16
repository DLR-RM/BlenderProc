import mathutils
import random

from src.main.Provider import Provider

class Uniform3d(Provider):
    """ Uniformly samples a 3-dimensional value.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "min", "A list of three values, describing the minimum values for 1st, 2nd, and 3rd dimensions."
       "max", "A list of three values, describing the maximum values for 1st, 2nd, and 3rd dimensions."

    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :param config: A configuration object containing the parameters necessary to sample.
        :return: Sampled value. Type: Mathutils Vector
        """
        # minimum values vector
        min = self.config.get_vector3d("min")
        # maximum values vector
        max = self.config.get_vector3d("max")

        position = mathutils.Vector()
        for i in range(3):
            position[i] = random.uniform(min[i], max[i])

        return position
