import numpy as np
from typing import Union, List

from mathutils import Vector

def shell(center: Union[Vector, np.ndarray, List[float]], radius_min: float, radius_max: float, elevation_min: float = -90,
          elevation_max: float = 90, azimuth_min: float = -180, azimuth_max: float = 180, uniform_volume: bool = False) -> np.ndarray:
    """ Samples a point from the volume between two spheres (radius_min, radius_max). Optionally the spheres can be constraint by setting 
          elevation and azimuth angles. E.g. if you only want to sample in the upper hemisphere set elevation_min = 0.

    :param center: Center shared by both spheres.
    :param radius_min: Radius of the smaller sphere.
    :param radius_max: Radius of the bigger sphere.
    :param elevation_min: Minimum angle of elevation in degrees. Range: [-90, 90].
    :param elevation_max: Maximum angle of elevation in degrees. Range: [-90, 90].
    :param azimuth_min: Minimum angle of azimuth in degrees. Range: [-180, 180].
    :param azimuth_max: Maximum angle of azimuth in degrees. Range: [-180, 180].
    :param uniform_volume: Instead of sampling the angles and radius uniformly, sample the shell volume uniformly.
                           As a result, there will be more samples at larger radii.
    :return: A sampled point.
    """
    
    center = np.array(center)
    
    assert -180 <= azimuth_min <= 180, "azimuth_min must be in range [-180, 180]"
    assert -180 <= azimuth_max <= 180, "azimuth_max must be in range [-180, 180]"
    assert -90 <= elevation_min <= 90, "elevation_min must be in range [-90, 90]"
    assert -90 <= elevation_min <= 90, "elevation_max must be in range [-90, 90]"
    assert azimuth_min < azimuth_max, "azimuth_min must be smaller than azimuth_max"
    assert elevation_min < elevation_max, "elevation_min must be smaller than elevation_max"
    
    if uniform_volume:
         
        radius = radius_min + (radius_max - radius_min) * np.cbrt(np.random.rand())
        
        # rejection sampling
        constr_fulfilled = False
        while not constr_fulfilled:
            direction_vector = np.random.randn(3)
            direction_vector /= np.linalg.norm(direction_vector)
            
            # https://stackoverflow.com/questions/4116658/faster-numpy-cartesian-to-spherical-coordinate-conversion
            xy = direction_vector[0]*direction_vector[0] + direction_vector[1]*direction_vector[1]
            elevation = np.arctan2(direction_vector[2], np.sqrt(xy))
            azimuth = np.arctan2(direction_vector[1], direction_vector[0])

            elev_constraint = np.deg2rad(elevation_min) < elevation < np.deg2rad(elevation_max)
            azim_constraint = np.deg2rad(azimuth_min) < azimuth < np.deg2rad(azimuth_max)
            constr_fulfilled = elev_constraint and azim_constraint
    else:
        el_sampled = np.deg2rad(elevation_min + (elevation_max - elevation_min) * np.random.rand())
        az_sampled = np.deg2rad(azimuth_min + (azimuth_max - azimuth_min) * np.random.rand())
        # spherical to cartesian coordinates
        direction_vector = np.array([np.sin(np.pi / 2 - el_sampled) * np.cos(az_sampled),
                                     np.sin(np.pi / 2 - el_sampled) * np.sin(az_sampled),
                                     np.cos(np.pi / 2 - el_sampled)])

        # Calculate the uniform radius
        radius = np.random.uniform(radius_min, radius_max)
        
    # Get the coordinates of a sampled point inside the shell
    position = direction_vector * radius + center

    return position
