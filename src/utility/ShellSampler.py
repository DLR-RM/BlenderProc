import numpy as np
import mathutils

class ShellSampler(object):

    def __init__(self):
        object.__init__():

    @staticmethod
    def sample(config):
        """

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
        # Set correct rejection radius
        if mode == "FULL":
            rejection_radius = 0
        elif mode == "RIM":
            rejection_radius = config.get_float("rejection_radius")
        else:
            raise Exception("Unknown sampling mode: " + mode)
        
        
        # Base angle of a sampling right cone
        base_angle = (180 - opening_angle)/2
        # Height of a sampling cone
        H = 1

        # Sampling a point from a 2-ball (disk) i.e. from the base of the right sampling cone using Polar + Radial CDF method + rejection for the rejection 2-ball if applicable
        sampled_point = center[0:2]
        while (sampled_point[0]- center[0])**2+(sampled_point[1]-center[1])**2<=rejection_radius**2:
            R = H * np.tan(base_angle)
            r = R * np.sqrt(np.random.uniform())
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
        


