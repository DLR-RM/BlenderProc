import numpy as np
from typing import Union

from mathutils import Vector

def sphere(center: Union[Vector, np.ndarray, list], radius: float, mode: str) -> np.ndarray:
    """ Samples a point from the surface or from the interior of solid sphere.

    https://math.stackexchange.com/a/87238
    https://math.stackexchange.com/a/1585996

    Example 1: Sample a point from the surface of the solid sphere of a defined radius and center location.

    .. code-block:: python

        Sphere.sample(
            center=Vector([0, 0, 0]),
            radius=2,
            mode="SURFACE"
        )

    :param center: Location of the center of the sphere.
    :param radius: The radius of the sphere.
    :param mode: Mode of sampling. Determines the geometrical structure used for sampling. Available: SURFACE (sampling
                 from the 2-sphere), INTERIOR (sampling from the 3-ball).
    """
    center = np.array(center)

    # Sample
    direction = np.random.normal(loc=0.0, scale=1.0, size=3)

    if np.count_nonzero(direction) == 0:  # Check no division by zero
        direction[0] = 1e-5

    # For normalization
    norm = np.sqrt(direction.dot(direction))

    # If sampling from the surface set magnitude to radius of the sphere
    if mode == "SURFACE":
        magnitude = radius
    # If sampling from the interior set it to scaled radius
    elif mode == "INTERIOR":
        magnitude = radius * np.cbrt(np.random.uniform())
    else:
        raise Exception("Unknown sampling mode: " + mode)

    # Normalize
    sampled_point = list(map(lambda x: magnitude*x/norm, direction))

    # Add center
    location = np.array(sampled_point) + center

    return location
