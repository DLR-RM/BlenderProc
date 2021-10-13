import random

import mathutils

from blenderproc.python.modules.main.Provider import Provider


class Color(Provider):
    """
    Uniformly samples a 4-dimensional RGBA vector.

    Example 1: Sample a RGBA grey color value using [min, max] range.

    .. code-block:: yaml

        {
          "provider": "sampler.Color",
          "min": [0, 0, 0, 1],
          "max": [1, 1, 1, 1],
          "grey": True,
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - min
          - A list of four values, describing the minimum values of R, G, B and A components. Range: [0; 1].
          - list
        * - max
          - A list of four values, describing the maximum values of R, G, B and A components. Range: [0; 1].
          - list
        * - grey
          - Sample grey values only. Default: False.
          - bool
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Samples a RGBA vector uniformly for each component.

        :return: RGBA vector. Type: mathutils.Vector
        """
        # minimum values vector
        min = self.config.get_vector4d("min")
        # maximum values vector
        max = self.config.get_vector4d("max")
        # sample only grey values
        grey = self.config.get_bool("grey", False)

        color = mathutils.Vector([0, 0, 0, 0])
        for i in range(4):
            if 0 <= min[i] <= 1 and 0 <= max[i] <= 1:
                if grey and 0 < i < 3:
                    color[i] = color[i-1]
                else:
                    color[i] = random.uniform(min[i], max[i])
            else:
                raise RuntimeError("min and max vectors must be composed of values in [0, 1] range!")

        return color
