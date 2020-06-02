import mathutils
import numpy as np

from src.main.Provider import Provider


class Shell(Provider):
    """ Samples a point from the space in between two spheres with a double spherical angle with apex in the center
        of those two spheres. Has option for uniform elevation sampling.

        Example 1: Sample a point from a space in between two structure-defining spheres defined by min and max radii,
        that lies in the sampling cone and not in the rejection cone defined by the min and max elevation degrees.

        {
          "provider": "sampler.Shell",
          "center": [0, 0, -0.8],
          "radius_min": 1,
          "radius_max": 4,
          "elevation_min": 40,
          "elevation_max": 89
        }


    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "center", "Center which is shared by both structure-defining spheres. Type: mathutils.Vector."
        "radius_min", "Radius of a smaller sphere. Type: float."
        "radius_max", "Radius of a bigger sphere. Type: float."
        "elevation_min", "Minimum angle of elevation in degrees: defines slant height of the sampling cone. "
                         "Type: float. Range: [0, 90]."
        "elevation_max", "Maximum angle of elevation in degrees: defines slant height of the rejection cone. "
                         "Type: float. Range: [0, 90]."
        "uniform_elevation", "Uniformly sample elevation angles. Type: bool. Default: False"
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
        elevation_max = self.config.get_float("elevation_max")

        if self.config.get_bool("uniform_elevation", False):
            el_sampled = np.deg2rad(elevation_min + (elevation_max-elevation_min) * np.random.rand())
            az_sampled = 2 * np.pi * np.random.rand()
            # spherical to cartesian coordinates
            direction_vector = np.array([np.sin(np.pi/2 - el_sampled) * np.cos(az_sampled), 
                                         np.sin(np.pi/2 - el_sampled) * np.sin(az_sampled), 
                                         np.cos(np.pi/2 - el_sampled)])
        else:
            if elevation_min == 0:
                # here comes the magic number
                elevation_min = 0.001
            if elevation_max == 90:
                # behold! magic number
                elevation_max = 0.001

            # Height of a sampling cone
            cone_height = 1
            
            # Sampling and rejection radius
            R_sampling = cone_height / np.tan(np.deg2rad(elevation_min))
            R_rejection = cone_height / np.tan(np.deg2rad(elevation_max))
            # Init sampled point at the center of a sampling disk
            sampled_2d = np.array([center[0], center[1]])
            
            # Sampling a point from a 2-ball (disk) i.e. from the base of the right subsampling
            # cone using Polar + Radial CDF method + rejection for 2-ball base of the rejection cone.

            while np.sum((sampled_2d - center[:2])**2) <= R_rejection**2:
                # http://extremelearning.com.au/how-to-generate-uniformly-random-points-on-n-spheres-and-n-balls/
                r = R_sampling * np.sqrt(np.random.uniform())
                theta = np.random.uniform() * 2 * np.pi
                sampled_2d[0] = center[0] + r * np.cos(theta)
                sampled_2d[1] = center[1] + r * np.sin(theta)

            # Sampled point in 3d
            direction_point = np.array([center[0] + sampled_2d[0], center[1] + sampled_2d[1], center[2] + cone_height])

            # Getting vector, then unit vector that defines the direction
            full_vector = direction_point - center

            direction_vector = full_vector/np.maximum(np.linalg.norm(full_vector), np.finfo(np.float32).eps)

        # Calculate the factor for the unit vector
        factor = np.random.uniform(radius_min, radius_max)
        # Get the coordinates of a sampled point inside the shell
        position = mathutils.Vector(direction_vector * factor + center)
        
        return position
