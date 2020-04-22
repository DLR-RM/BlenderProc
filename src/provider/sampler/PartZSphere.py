import numpy as np

from src.main.Provider import Provider
from src.provider.sampler.Sphere import Sphere

class PartZSphere(Provider):
    """ Samples a point from the surface or from the interior of solid sphere

    Gaussian is spherically symmetric. Sample from three independent Gaussian distributions
    the direction of the vector inside the sphere. Then calculate magnitude based on the operation mode.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "center", "A list of three values, describing the x, y and z coordinate of the center of the sphere."
       "radius", "The radius of the sphere."
       "mode", "Mode of sampling. SURFACE - sampling from the 2-sphere, INTERIOR - sampling from the 3-ball."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    # https://math.stackexchange.com/a/87238
    # https://math.stackexchange.com/a/1585996
    def run(self):
        """
        :param config: A configuration object containing the parameters necessary to sample.
        :return: A random point lying inside or on the surface of a solid sphere. Type: Mathutils vector
        """
        # Center of the sphere.
        center = np.array(self.config.get_list("center"))
        # Radius of the sphere.
        radius = self.config.get_float("radius")
        # Mode of operation.
        mode = self.config.get_string("mode")
        z_above_center = self.config.get_float("z_above_center")

        if z_above_center >= radius:
            raise Exception("The z_above_center value is bigger or as big as the radius!")
        while True:
            location = Sphere.sample(center, radius, mode)
            if location[2] > center[2] + z_above_center:
                return location
