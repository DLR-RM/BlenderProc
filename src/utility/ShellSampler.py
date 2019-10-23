import numpy as np
import mathutils

class ShellSampler(object):
        """ 
         Samples a point from the space in between two spheres with a spherical angle (sampling cone) with apex in the center of those two spheres.
        Sample a point on the disk that is a base of a subsampling cone defined by opening angle of the sampling cone. Then calculate a direction to this point, sample a factor for a resulting vector uniformly, then get a location.

        **Configuration**:

        .. csv-table::
           :header: "Parameter", "Description"

           "config", "A configuration object containing the parameters necessary to sample."

        **Sampling settings**

        .. csv-table::
           :header: "Keyword", "Description"

           "center", "Center of two spheres."
           "radius_min", "Radius of a smaller sphere."
           "radius_max", "Radius of a bigger sphere."
           "opening_angle", "Opening angle of a sampling cone."
           "mode", "Mode of operation: With rejection of 2d points that lie in the base of a subsampling rejection cone defined with a radius based on a rejection_parameter. Mode without rejection: "FULL", with rejection: "RIM"."
           "rejection_factor", "Factor used to calculate the radius of a rejection subsampling cone."
        """

    def __init__(self):
        object.__init__():

    @staticmethod
    def sample(config):
        """ Sample a point from a shell of two spheres with a sampling cone.

        :param config: A configuration object containing the parameters required to perform sampling.
        :return: A sampled point. Type: Mathutils vector.
        """
        # Center of both spheres
        center = np.array(config.get_list("center"))
        # Radius of a smaller sphere
        radius_min = config.get_float("radius_min")
        # Radius of a bigger sphere
        radius_max = config.get_float("radius_max")
        # Opening angle of a right circular cone
        opening_angle = config.get_float("opening_angle")
        # Mode of sampling
        mode = config.get_string("mode")
        # Set correct rejection factor
        if mode == "FULL":
            rejection_factor = 0
        elif mode == "RIM":
            rejection_factor = config.get_float("rejection_factor")
            if rejection_factor >= 1:
                rejection_factor = 0.9
        else:
            raise Exception("Unknown sampling mode: " + mode)
        
        
        # Base angle of a sampling right cone
        base_angle = (180 - opening_angle)/2
        # Height of a sampling cone
        H = 1

        # Sampling a point from a 2-ball (disk) i.e. from the base of the right sampling cone using Polar + Radial CDF method + rejection for 2-ball
        sampled_point = center[0:2]
        reejction_radius = 0
        while (sampled_point[0] - center[0])**2 + (sampled_point[1] - center[1])**2 <= rejection_radius**2:
            R = H * np.tan(base_angle)
            r = R * np.sqrt(np.random.uniform())
            rejection_radius = R * rejection_factor
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
