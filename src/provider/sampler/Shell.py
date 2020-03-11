import numpy as np
import mathutils

from src.main.Provider import Provider

class Shell(Provider):
    """ Samples a point from the space in between two spheres with a spherical angle (sampling cone) with apex in the center of those two spheres.

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "center", "Center of two spheres."
        "radius_min", "Radius of a smaller sphere. Units: meters."
        "radius_max", "Radius of a bigger sphere. Units: meters."
        "elevation_min", "Minimum angle of elevation: defines slant height of the sampling cone. Units: degrees."
        "elevation_max", "Maximum angle of elevation: defines slant height of the rejection cone. Units: degrees."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Sample a point from a space in between two halfspheres with the same center point and a sampling cone with apex in this center.

        :param config: A configuration object containing the parameters required to perform sampling.
        :return: A sampled point. Type: Mathutils vector.
        """
        # Center of both spheres
        center = np.array(self.config.get_list("center"))
        # Radius of a smaller sphere
        radius_min = self.config.get_float("radius_min")
        # Radius of a bigger sphere
        radius_max = self.config.get_float("radius_max")
        # Elevation angles
        elevation_min = self.config.get_float("elevation_min")
        if elevation_min == 0:
            # here comes the magic number
            elevation_min = 0.001
        elevation_max = self.config.get_float("elevation_max")
        if elevation_max == 90:
            # behold! magic number
            elevation_max = 0.001
        # Height of a sampling cone
        H = 1
        
        # Sampling and rejection radius
        R_sampling = H / np.tan(np.deg2rad(elevation_min))
        R_rejection = H / np.tan(np.deg2rad(elevation_max))
        # Init sampled point at the center of a sampling disk
        sampled_2d = [center[0], center[1]]
        
        # Sampling a point from a 2-ball (disk) i.e. from the base of the right subsampling
        # cone using Polar + Radial CDF method + rejection for 2-ball base of the rejection cone.
        while (sampled_2d[0] - center[0])**2 + (sampled_2d[1] - center[1])**2 <= R_rejection**2:
        # http://extremelearning.com.au/how-to-generate-uniformly-random-points-on-n-spheres-and-n-balls/
            r = R_sampling * np.sqrt(np.random.uniform())
            theta = np.random.uniform() * 2 * np.pi
            sampled_2d[0] = center[0] + r * np.cos(theta)
            sampled_2d[1] = center[1] + r * np.sin(theta)

        # Sampled point in 3d
        direction_point = np.array([center[0] + sampled_2d[0], center[1] + sampled_2d[1], center[2] + H])
        # Getting vector, then unit vector that defines the direction
        full_vector = direction_point - center
        direction_vector = full_vector/np.linalg.norm(full_vector)
        # Calculate the factor for the unit vector
        factor = np.random.uniform(radius_min, radius_max)
        # Get the coordinates of a sampled point inside the shell
        position = mathutils.Vector(direction_vector * factor + center)
        
        return position
