import numpy as np
import mathutils

from src.main.Provider import Provider

class Disk(Provider):
    """ Samples a point from the 2d circle or from the disk in 3d space.

    **Configuration**:

    .. csv-table::
       :header:, "Parameter", "Description"

       "center", "A list of three values, describing x, y and z coordinates of the center of a 2-ball. "
       "radius", "The radius of the disk."
       "mode", "Mode of sampling. CIRCLE - sampling from the 1-sphere, DISK - sampling from the 2-ball (default mode)."
       "up_vector", "An up vector which specifies a local coordinate system of the disk."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :param config: A configuration object containing the parameters necessary to sample.
        :return: A random point lying inside or on the surface of a solid sphere. Type: Mathutils vector
        """
        # Center of the disk.
        center = self.config.get_vector3d("center")
        # Radius of the disk.
        radius = self.config.get_float("radius")
        # Mode of operation.
        mode = self.config.get_string("mode", "DISK")
        # Up vector
        up_vector = self.config.get_vector3d("up_vector", [0, 0, 1])
        # Sample directions
        direction = np.random.normal(size=2)

        if np.count_nonzero(direction)==0:
            direction[0] = 1e-5

        # For normalization
        norm = np.sqrt(direction.dot(direction))

        # If sampling from the circle set magnitude to radius of the disk
        if mode == "CIRCLE":
            magnitude = radius
        # If sampling from a disk set it to scaled radius
        elif mode == "DISK":
            magnitude = radius * np.sqrt(np.random.uniform())
        else:
            raise Exception("Unknown sampling mode: " + mode)

        # Normilize and transform to 3d
        sampled_point = np.append(list(map(lambda x: magnitude*x/norm, direction)), 0)
        
        # Get Euler angles from up vector
        euler_angles = up_vector.to_track_quat('Z', 'Y').to_euler()
        # Get rotation
        rot_mat = mathutils.Euler((euler_angles), 'XYZ')
        # Get location on a rotated disk and add center
        location = rot @ mathutils.Vector(sampled_point) + center

        return location
