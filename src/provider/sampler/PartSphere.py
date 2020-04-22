import numpy as np

from src.main.Provider import Provider
from src.provider.sampler.Sphere import Sphere

class PartSphere(Provider):
    """ Samples a point from the surface or from the interior of solid sphere

    Gaussian is spherically symmetric. Sample from three independent Gaussian distributions
    the direction of the vector inside the sphere. Then calculate magnitude based on the operation mode.

    The Sphere is split along the part_sphere_vector, this gives two sphere parts. The distance is used to define
    the half, which is used.

    For example:

    If the vector is parallel to the z-axis, the distance check is: sampled_location[2] > distance_above_center.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "center", "A list of three values, describing the x, y and z coordinate of the center of the sphere. Type: mathutils.Vector"
       "radius", "The radius of the sphere. Type: float"
       "mode", "Mode of sampling. SURFACE - sampling from the 2-sphere, INTERIOR - sampling from the 3-ball. Type: str"
       "distance_above_center", "The distance above the center, which should be used, Type: float, default: 0.0 (half of the sphere)"
       "part_sphere_vector", "The direction in which the sphere should be split, the end point of the vector, will be"
                             "in the middle of the sphere pointing towards the middle of the resulting surface."
                             "Type: mathutils.Vector, Default: [0,0,1]"
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
        dist_above_center = self.config.get_float("distance_above_center", 0.0)
        part_sphere_dir_vector = self.config.get_vector3d("part_sphere_vector", [0, 0, 1])
        part_sphere_dir_vector.normalize()

        if dist_above_center >= radius:
            raise Exception("The dist_above_center value is bigger or as big as the radius!")

        while True:
            location = Sphere.sample(center, radius, mode)
            # project the location onto the part_sphere_dir_vector and get the length
            length = location.dot(part_sphere_dir_vector)
            if length > dist_above_center:
                return location
