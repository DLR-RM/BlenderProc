import numpy as np

from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.sampler.Sphere import sphere


class SphereModule(Provider):
    """
    Samples a point from the surface or from the interior of solid sphere

    Example 1: Sample a point from the surface of the solid sphere of a defined radius and center location.

    .. code-block:: yaml

        {
          "provider":"sampler.Sphere",
          "center":[0, 0, 0],
          "radius": 2,
          "mode": "SURFACE"
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - center
          - Location of the center of the sphere.
          - mathutils.Vector
        * - radius
          - The radius of the sphere.
          - float
        * - mode
          - Mode of sampling. Determines the geometrical structure used for sampling. Available: SURFACE (sampling
            from the 2-sphere), INTERIOR (sampling from the 3-ball).
          - string
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    # https://math.stackexchange.com/a/87238
    # https://math.stackexchange.com/a/1585996
    def run(self):
        """
        :param config: A configuration object containing the parameters necessary to sample.
        :return: A random point lying inside or on the surface of a solid sphere. Type: mathutils.Vector
        """
        # Center of the sphere.
        center = np.array(self.config.get_list("center"))
        # Radius of the sphere.
        radius = self.config.get_float("radius")
        # Mode of operation.
        mode = self.config.get_string("mode")

        return sphere(center, radius, mode)

