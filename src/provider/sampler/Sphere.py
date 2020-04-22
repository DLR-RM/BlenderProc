import numpy as np
import mathutils

from src.main.Provider import Provider

class Sphere(Provider):
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

        return Sphere.sample(center, radius, mode)

    @staticmethod
    def sample(center, radius, mode):
        """
        Samples a point according to the mode, the center and the radius.

       :param center, A list of three values, describing the x, y and z coordinate of the center of the sphere.
       :param radius, The radius of the sphere.
       :param mode, Mode of sampling. SURFACE - sampling from the 2-sphere, INTERIOR - sampling from the 3-ball.
        """
        # Sample
        direction = np.random.normal(size=3)
        
        if np.count_nonzero(direction) == 0:  # Check no division by zero
            direction[0] = 1e-5

        # For normalization
        norm = np.sqrt(direction.dot(direction))

        # If sampling from the surface set magnitude to radius of the sphere
        if mode == "SURFACE":
            magnitude = radius
        # If sampling from the interior set it to scaled radius
        elif mode == "INTERIOR":
            magnitude = radius * np.cbrt(np.random.unform())
        else:
            raise Exception("Unknown sampling mode: " + mode)
        
        # Normalize
        sampled_point = list(map(lambda x: magnitude*x/norm, direction))
        
        # Add center
        location = mathutils.Vector(np.array(sampled_point) + center)

        return location
