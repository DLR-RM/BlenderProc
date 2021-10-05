import numpy as np
from typing import Union, List

from mathutils import Vector


def shell(center: Union[Vector, np.ndarray, List[float]], radius_min: float, radius_max: float, elevation_min: float,
          elevation_max: float, uniform_elevation: bool = False) -> np.ndarray:
    """ Samples a point from the space in between two spheres with a double spherical angle with apex in the center
        of those two spheres. Has option for uniform elevation sampling.

    Example 1: Sample a point from a space in between two structure-defining spheres defined by min and max radii,
    that lies in the sampling cone and not in the rejection cone defined by the min and max elevation degrees.

    .. code-block:: python

        sampler.Shell(
            center=[0, 0, -0.8],
            radius_min=1,
            radius_max=4,
            elevation_min=40,
            elevation_max=89
        )

    :param center: Center which is shared by both structure-defining spheres.
    :param radius_min: Radius of a smaller sphere.
    :param radius_max: Radius of a bigger sphere.
    :param elevation_min: Minimum angle of elevation in degrees: defines slant height of the sampling cone. Range: [0, 90].
    :param elevation_max: Maximum angle of elevation in degrees: defines slant height of the rejection cone. Range: [0, 90].
    :param uniform_elevation: Uniformly sample elevation angles.
    :return: A sampled point.
    """
    center = np.array(center)

    if uniform_elevation:
        el_sampled = np.deg2rad(elevation_min + (elevation_max - elevation_min) * np.random.rand())
        az_sampled = 2 * np.pi * np.random.rand()
        # spherical to cartesian coordinates
        direction_vector = np.array([np.sin(np.pi / 2 - el_sampled) * np.cos(az_sampled),
                                     np.sin(np.pi / 2 - el_sampled) * np.sin(az_sampled),
                                     np.cos(np.pi / 2 - el_sampled)])
    else:
        if elevation_min == 0:
            # here comes the magic number
            elevation_min = 0.001
        if elevation_max == 90:
            # behold! magic number
            elevation_max = 0.001

        # Height of a sampling cone
        cone_height = 1

        # Sampling and rejection radius
        r_sampling = cone_height / np.tan(np.deg2rad(elevation_min))
        r_rejection = cone_height / np.tan(np.deg2rad(elevation_max))
        # Init sampled point at the center of a sampling disk
        sampled_2d = np.array([center[0], center[1]])

        # Sampling a point from a 2-ball (disk) i.e. from the base of the right subsampling
        # cone using Polar + Radial CDF method + rejection for 2-ball base of the rejection cone.

        while np.sum((sampled_2d - center[:2]) ** 2) <= r_rejection ** 2:
            # http://extremelearning.com.au/how-to-generate-uniformly-random-points-on-n-spheres-and-n-balls/
            r = r_sampling * np.sqrt(np.random.uniform())
            theta = np.random.uniform() * 2 * np.pi
            sampled_2d[0] = center[0] + r * np.cos(theta)
            sampled_2d[1] = center[1] + r * np.sin(theta)

        # Sampled point in 3d
        direction_point = np.array([center[0] + sampled_2d[0], center[1] + sampled_2d[1], center[2] + cone_height])

        # Getting vector, then unit vector that defines the direction
        full_vector = direction_point - center

        direction_vector = full_vector / np.maximum(np.linalg.norm(full_vector), np.finfo(np.float32).eps)

    # Calculate the factor for the unit vector
    factor = np.random.uniform(radius_min, radius_max, size=None)
    # Get the coordinates of a sampled point inside the shell
    position = direction_vector * factor + center

    return position
