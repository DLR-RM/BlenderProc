import mathutils
import random
import numpy as np

from src.main.Provider import Provider


class UniformSO3(Provider):
    """ Uniformly samples rotations from SO(3). Allows to limit the rotation around Blender World coordinate axes.

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "around_x", "Whether to rotate around X-axis. Type: bool. Default: True."
        "around_y", "Whether to rotate around Y-axis. Type: bool. Default: True."
        "around_z", "Whether to rotate around Z-axis. Type: bool. Default: True."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Sampled rotation in euler angles. Type: Mathutils Vector
        """
        # Indicators of which axes to rotate around.
        around_x = self.config.get_bool('around_x', True)
        around_y = self.config.get_bool('around_y', True)
        around_z = self.config.get_bool('around_z', True)

        # Uniform sampling in full SO3.
        if around_x and around_y and around_z:
            quat_rand = self._random_quaternion()
            euler_rand = mathutils.Quaternion(quat_rand).to_euler()

        # Uniform sampling of angles around the selected axes.
        else:
            def random_angle():
                return random.uniform(0, 2 * np.pi)
            mat_rand = mathutils.Matrix.Identity(3)
            if around_x:
                mat_rand @= mathutils.Matrix.Rotation(random_angle(), 3, 'X')
            if around_y:
                mat_rand @= mathutils.Matrix.Rotation(random_angle(), 3, 'Y')
            if around_z:
                mat_rand @= mathutils.Matrix.Rotation(random_angle(), 3, 'Z')
            euler_rand = mat_rand.to_euler()

        return mathutils.Vector(euler_rand)

    def _random_quaternion(self, rand=None):
        """ Return uniform random unit quaternion.

        https://github.com/thodan/bop_toolkit/blob/master/bop_toolkit_lib/transform.py

        :param rand: Three independent random variables that are uniformly distributed between 0 and 1. Type: list.
        :return: Unit quaternion. Type: np.array.
        """
        if rand is None:
            rand = np.random.rand(3)
        else:
            assert len(rand) == 3

        r1 = np.sqrt(1.0 - rand[0])
        r2 = np.sqrt(rand[0])
        pi2 = np.pi * 2.0
        t1 = pi2 * rand[1]
        t2 = pi2 * rand[2]

        return np.array([np.cos(t2) * r2, np.sin(t1) * r1,
                            np.cos(t1) * r1, np.sin(t2) * r2])
