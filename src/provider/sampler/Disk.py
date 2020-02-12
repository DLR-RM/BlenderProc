import numpy as np
import mathutils

from src.main.Provider import Provider

class Disk(Provider):
    """ Samples a point on a 1-sphere (circle) or on a 2-ball (disk, i.e. circle + interior space).

    **Configuration**:

    .. csv-table::
       :header:, "Parameter", "Description"

       "center", "Center of a disk. Type: mathutils Vector."
       "radius", "The radius of the disk. Type: float."
       "use_circle_only", "Mode of sampling, i.e. which geometric shape to sample from.  Optional. Type: boolean. Default value: False (sampling from a disk)."
       "up_vector", "An up vector which specifies a local coordinate system of the disk. Optional. Type: mathutils Vector. Default value: [0, 0, 1]"
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: A random point sampled point on a 1-sphere (circle) or on a 2-ball (disk). Type: Mathutils vector.
        """
        # Center of the disk.
        center = self.config.get_vector3d("center")
        # Radius of the disk.
        radius = self.config.get_float("radius")
        # Mode of operation.
        use_circle_only = self.config.get_bool("use_circle_only", False)
        # Up vector
        up_vector = self.config.get_vector3d("up_vector", [0, 0, 1])
        # Sample directions
        direction = np.random.normal(size=2)

        if np.count_nonzero(direction)==0:
            direction[0] = 1e-5

        # For normalization
        norm = np.sqrt(direction.dot(direction))

        # If sampling from the circle set magnitude to radius of the disk
        if use_circle_only:
            magnitude = radius
        # If sampling from a disk set it to scaled radius
        else:
            magnitude = radius * np.sqrt(np.random.uniform())

        # Normalize and transform to 3d
        sampled_point = np.append(list(map(lambda x: magnitude*x/norm, direction)), 0)
        
        # Get Euler angles from up vector
        euler_angles = up_vector.to_track_quat('Z', 'Y').to_euler()
        # Get rotation
        rot_mat = mathutils.Euler(euler_angles, 'XYZ').to_matrix()
        # Get location on a rotated disk and add center
        location = rot_mat @ mathutils.Vector(sampled_point) + center

        return location
