import numpy as np

from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.sampler.Shell import shell


class ShellModule(Provider):
    """
    Samples a point from the space in between two spheres with a double spherical angle with apex in the center
    of those two spheres. Has option for uniform elevation sampling.

    Example 1: Sample a point from a space in between two structure-defining spheres defined by min and max radii,
    that lies in the sampling cone and not in the rejection cone defined by the min and max elevation degrees.

    .. code-block:: yaml

        {
          "provider": "sampler.Shell",
          "center": [0, 0, -0.8],
          "radius_min": 1,
          "radius_max": 4,
          "elevation_min": 40,
          "elevation_max": 89
        }


    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - center
          - Center which is shared by both structure-defining spheres.
          - mathutils.Vector
        * - radius_min
          - Radius of a smaller sphere.
          - float
        * - radius_max
          - Radius of a bigger sphere.
          - float
        * - elevation_min
          - Minimum angle of elevation in degrees: defines slant height of the sampling cone. Range: [0, 90].
          - float
        * - elevation_max
          - Maximum angle of elevation in degrees: defines slant height of the rejection cone. Range: [0, 90].
          - float
        * - uniform_elevation
          - Uniformly sample elevation angles. Default: False
          - bool
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Sample a point from a space in between two halfspheres with the same center point and a sampling cone with apex in this center.

        :return: A sampled point. Type: mathutils.Vector.
        """
        # Center of both spheres
        center = np.array(self.config.get_list("center"))
        # Radius of a smaller sphere
        radius_min = self.config.get_float("radius_min")
        # Radius of a bigger sphere
        radius_max = self.config.get_float("radius_max")
        # Elevation angles
        elevation_min = self.config.get_float("elevation_min")
        elevation_max = self.config.get_float("elevation_max")
        uniform_elevation = self.config.get_bool("uniform_elevation", False)

        return shell(
            center=center,
            radius_min=radius_min,
            radius_max=radius_max,
            elevation_min=elevation_min,
            elevation_max=elevation_max,
            uniform_elevation=uniform_elevation
        )