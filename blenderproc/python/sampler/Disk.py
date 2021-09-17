from typing import Union, List

import mathutils
import numpy as np
from mathutils import Vector


def disk(center: Union[Vector, np.ndarray, List[float]], radius: float, rotation: Union[Vector, np.ndarray, List[float]] = None,
         sample_from: str = "disk", start_angle: float = 0, end_angle: float = 180) -> np.ndarray:
    """ Samples a point on a 1-sphere (circle), or on a 2-ball (disk, i.e. circle + interior space), or on an arc/sector
        with an inner angle less or equal than 180 degrees. Returns a 3d mathutils.Vector sampled point.

    Example 1: Sample a point from a 1-sphere.

    .. code-block:: python

        Disk.sample(
            center=[0, 0, 4],
            radius=7,
            sample_from="circle"
        )

    Example 2: Sample a point from a sector.

    .. code-block:: python

        Disk.sample(
            center=[0, 0, 4],
            radius=7,
            sample_from="sector",
            start_angle=0,
            end_angle=90
        )

    :param center: Center (in 3d space) of a 2d geometrical shape to sample from.
    :param radius: The radius of the disk.
    :param rotation: List of three (XYZ) Euler angles that represent the rotation of the 2d geometrical structure used for
                     sampling in 3d space.
    :param sample_from: Mode of sampling. Defines the geometrical structure used for sampling, i.e. the shape to sample from.
    :param start_angle: Start angle in degrees that is used to define a sector/arc to sample from. Must be smaller than
                        end_angle. Arc's/sector's inner angle (between start and end) must be less or equal than 180 degrees.
                        Angle increases in the counterclockwise direction from the positive direction of X axis.
    :param end_angle: End angle in degrees that is used to define a sector/arc to sample from. Must be bigger than
                      start_angle. Arc's/sector's inner angle (between start and end) must be less or equal than 180 degrees.
                      Angle increases in the counterclockwise direction from the positive direction of X axis.
    :return: A random point sampled point on a circle/disk/arc/sector.
    """
    if rotation is None:
        rotation = [0, 0, 0]

    # check if the mode/sampling structure is supported
    if sample_from not in ["disk", "circle", "sector", "arc"]:
        raise Exception("Unknown mode of operation: " + sample_from)
    # if mode is sampling from sector or arc
    if sample_from in ["arc", "sector"]:
        # check if start and end angles comply to boundaries
        if not all([start_angle < end_angle, abs(start_angle - end_angle) <= 180]):
            raise Exception("Sector's/arch's start and end points are defined wrong! Boundaries to comply with:"
                            "1. start_angle < end_angle; 2. abs(start_angle - end_angle) <= 180.")
        # transform to 2d vectors
        start_vec = [np.cos(np.deg2rad(start_angle)), np.sin(np.deg2rad(start_angle))]
        end_vec = [np.cos(np.deg2rad(end_angle)), np.sin(np.deg2rad(end_angle))]

    # if sampling from the circle or arc set magnitude to radius, if not - to the scaled radius
    if sample_from.lower() in ["circle", "arc"]:
        magnitude = radius
    elif sample_from.lower() in ["disk", "sector"]:
        magnitude = radius * np.sqrt(np.random.uniform())
    else:
        raise Exception("Unknown mode of operation: " + sample_from)

    sampled_point = Disk._sample_point(magnitude)

    # sample a point until it falls into the defined sector/arc
    if sample_from in ["arc", "sector"]:
        while not all([not Disk._is_clockwise(start_vec, sampled_point), Disk._is_clockwise(end_vec, sampled_point)]):
            sampled_point = Disk._sample_point(magnitude)

    # get rotation
    rot_mat = mathutils.Euler(rotation, 'XYZ').to_matrix()
    # apply rotation and add center
    location = np.array(rot_mat) @ sampled_point + np.array(center)

    return location


class Disk:

    @staticmethod
    def _sample_point(magnitude: float) -> np.ndarray:
        """ Samples a 3d point from a two-dimensional normal distribution with the third dim equal to 0.

        :param magnitude: Scaling factor of a radius.
        :return: Sampled 3d point. Type: numpy.array.
        """
        direction = np.random.normal(loc=0.0, scale=1.0, size=2)
        if np.count_nonzero(direction) == 0:
            direction[0] = 1e-5
        norm = np.sqrt(direction.dot(direction))
        sampled_point = np.append(list(map(lambda x: magnitude * x / norm, direction)), 0)

        return sampled_point

    @staticmethod
    def _is_clockwise(rel_point: Union[Vector, np.ndarray, List[float]],
                      sampled_point: Union[Vector, np.ndarray, List[float]]) -> bool:
        """ Checks if the sampled_point is in the clockwise direction in relation to the rel_point.

        :param rel_point: Point relative to which the test is performed.
        :param sampled_point: Point for which test is performed.
        :return: True if the sampled_point lies in the clockwise direction in relation to the rel_point, False if not.
        """
        return (-rel_point[0] * sampled_point[1] + rel_point[1] * sampled_point[0]) > 0
