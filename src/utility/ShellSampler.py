import numpy as np
import mathutils

class ShellSampler(object):
        """ 
         Samples a point from the space in between two spheres with a spherical angle (sampling cone) with apex in the center of those two spheres.
        Sample a point on the disk that is a base of a subsampling cone defined by opening angle of the sampling cone and a fixed height. Then calculate a direction to this point, sample a factor for a resulting vector uniformly, then get a location.

        **Configuration**:

        .. csv-table::
           :header: "Parameter", "Description"

           "config", "A configuration object containing the parameters required to perform sampling."

        **Sampling settings**

        .. csv-table::
           :header: "Keyword", "Description"

           "center", "Center of two spheres."
           "radius_min", "Radius of a smaller sphere."
           "radius_max", "Radius of a bigger sphere."
           "elevation_min", "Minimum angle of elevation: defines slant height of the sampling cone."
           "elevation_max", "Maximum angle of elevation: defines slant height of the rejection cone."
        """

    def __init__(self):
        object.__init__():

    @staticmethod
    def sample(config):
        """ Sample a point from a space shared by two halfspheres with the same center point and a sampling cone with apex in this center.

        :param config: A configuration object containing the parameters required to perform sampling.
        :return: A sampled point. Type: Mathutils vector.
        """
        # Center of both spheres
        center = np.array(config.get_list("center"))
        # Radius of a smaller sphere
        radius_min = config.get_float("radius_min")
        # Radius of a bigger sphere
        radius_max = config.get_float("radius_max")
        # Elevation angles
        elevation_min = config.get_float("elevation_min")
        elevation_max = config.get_float("elevation_max")
        
        # Height of a sampling cone
        H = 1
        # Base angle of a sampling right cone
        sampling_opening_angle = 180 - elevation_min * 2
        sampling_base_angle = 90 - sampling_opening_angle/2
        # Base angle of a rejection right cone
        rejection_opening_angle = 180 - elevation_max * 2
        if elevation_max == 90:
            rejection_base_angle = 0
        else:
            rejection_base_angle = 90 - rejection_opening_angle/2

        # Sampling and rejection radius
        R_sampling = H * np.tan(sampling_base_angle)
        R_rejection = H * np.tan(rejection_base_angle)

        # Init sampled point at the center of a sampling disk
        sampled_point = center[0:2]
        
        # Sampling a point from a 2-ball (disk) i.e. from the base of the right subsampling cone using Polar + Radial CDF method + rejection for 2-ball base of the rejection cone
        while (sampled_point[0] - center[0])**2 + (sampled_point[1] - center[1])**2 <= R_rejection**2:
            r = R_sampling * np.sqrt(np.random.uniform())
            theta = np.random.unifrom() * 2 * np.pi
            sampled_point[0] = center[0] + r * np.cos(theta)
            sampled_point[1] = center[1] + r * np.sin(theta)
        
        # Sampled point in 3d
        direction_point = np.array([center[0] + sampled_point[0], center[1] + sampled_point[1], center[2] + H])
        # Getting vector, then unit vector that defines the direction
        full_vector = direction_point - center
        direction_vector = full_vector/np.linalg.norm(full_vector)
        # Calculate the factor for the unit vector
        factor = np.random.uniform(radius_min, radius_max)
        # Get the coordinates of a sampled point inside the shell
        position = mathutils.Vector(direction_vector * factor + center)

        return position
