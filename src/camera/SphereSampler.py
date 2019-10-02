import numpy as np
import mathutils


class SphereSampler(object):

    def __init__(self):
        object.__init__()

    # https://math.stackexchange.com/a/87238
    # https://math.stackexchange.com/a/1585996
    def sample(self, center, radius):
        """
        Samples a point on and inside a solid sphere. Gaussian is spherically symmetric. Sample from three independent
        Guassian distributions the direction of the vector inside the sphere. Then sample from a uniform distribution
        a number from 0-1 to determine the magnitude, 1 means to lie on the surface and anything else inside.

        :param center: Center of the sphere. Type: ndarray
        :param radius: Length of the radius of the sphere.
        :return: A random point lying inside or on the surface of a solid sphere. Type: Mathutils vector
        """

        direction = np.random.normal(size=3)
        magnitude = radius * (np.cbrt(np.random.uniform()))

        if np.count_nonzero(direction) == 0:  # Check no division on zero
            direction[0] = 1e-5

        # Normalize and add center
        _position =  (magnitude * (direction / np.sqrt(direction.dot(direction)))) + center
        position = mathutils.Vector()
        for i in range(3):
            position[i] = _position[i]

        return position
