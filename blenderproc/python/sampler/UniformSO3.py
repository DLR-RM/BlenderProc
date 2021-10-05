from typing import List, Optional, Union

import mathutils
import random
import numpy as np


def uniformSO3(around_x: bool = True, around_y: bool = True, around_z: bool = True) -> np.ndarray:
    """ Uniformly samples rotations from SO(3). Allows to limit the rotation around Blender World coordinate axes.

    :param around_x: Whether to rotate around X-axis.
    :param around_y: Whether to rotate around Y-axis.
    :param around_z: Whether to rotate around Z-axis.
    :return: Sampled rotation in euler angles.
    """
    # Uniform sampling in full SO3.
    if around_x and around_y and around_z:
        quat_rand = UniformSO3._random_quaternion()
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

    return np.array(euler_rand)


class UniformSO3:
    @staticmethod
    def _random_quaternion(rand: Optional[Union[List[float], np.ndarray]] = None) -> np.ndarray:
        """ Return uniform random unit quaternion.

        https://github.com/thodan/bop_toolkit/blob/master/bop_toolkit_lib/transform.py

        :param rand: Three independent random variables that are uniformly distributed between 0 and 1.
        :return: Unit quaternion.
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

        return np.array([np.cos(t2) * r2, np.sin(t1) * r1, np.cos(t1) * r1, np.sin(t2) * r2])
