import mathutils
import random
import transforms3d
import numpy as np

from src.main.Provider import Provider

class UniformSO3(Provider):
    """ Uniformly samples rotations from SO(3)

    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Sampled rotation in euler angles. Type: Mathutils Vector
        """
        quat_rand = self._random_quaternion()
        euler_rand = mathutils.Quaternion(quat_rand).to_euler()

        return mathutils.Vector(euler_rand)

    def _random_quaternion(self, rand=None):
        """Return uniform random unit quaternion.

        rand: array like or None
            Three independent random variables that are uniformly distributed
            between 0 and 1.

        >>> q = _random_quaternion()
        >>> np.allclose(1, vector_norm(q))
        True
        >>> q = _random_quaternion(np.random.random(3))
        >>> len(q.shape), q.shape[0]==4
        (1, True)
        
        https://github.com/thodan/bop_toolkit/blob/master/bop_toolkit_lib/transform.py
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
