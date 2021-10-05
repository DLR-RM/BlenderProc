import math
import random
import numpy as np

from typing import List, Union, Optional, Tuple
from mathutils import Vector

from blenderproc.python.types.MeshObjectUtility import MeshObject


def upper_region(objects_to_sample_on: Union[MeshObject, List[MeshObject]],
                 face_sample_range: Optional[Union[Vector, np.ndarray, List[float]]] = None, min_height: float = 0.0,
                 max_height: float = 1.0, use_ray_trace_check: bool = False,
                 upper_dir: Optional[Union[Vector, np.ndarray, List[float]]] = None,
                 use_upper_dir: bool = True) -> np.ndarray:
    """ Uniformly samples 3-dimensional value over the bounding box of the specified objects (can be just a plane) in the
        defined upper direction. If "use_upper_dir" is False, samples along the face normal closest to "upper_dir". The
        sampling volume results in a parallelepiped. "min_height" and "max_height" define the sampling distance from the face.

    Example 1: Sample a location on the surface of the given objects with height above this
    surface in range of [1.5, 1.8].

    .. code-block:: python

        UpperRegionSampler.sample(
            objects_to_sample_on=objs,
            min_height=1.5,
            max_height=1.8
        )

    :param objects_to_sample_on: Objects, on which to sample on.
    :param face_sample_range: Restricts the area on the face where objects are sampled. Specifically describes relative lengths of
                              both face vectors between which points are sampled. Default: [0.0, 1.0]
    :param min_height: Minimum distance to the bounding box that a point is sampled on.
    :param max_height: Maximum distance to the bounding box that a point is sampled on.
    :param use_ray_trace_check: Toggles using a ray casting towards the sampled object (if the object is directly below the sampled
                                position is the position accepted).
    :param upper_dir: The 'up' direction of the sampling box. Default: [0.0, 0.0, 1.0].
    :param use_upper_dir: Toggles using a ray casting towards the sampled object (if the object is directly below the sampled
                          position is the position accepted).
    :return: Sampled value.
    """
    if face_sample_range is None:
        face_sample_range = [0.0, 1.0]
    if upper_dir is None:
        upper_dir = [0.0, 0.0, 1.0]

    face_sample_range = np.array(face_sample_range)
    upper_dir = np.array(upper_dir)
    upper_dir /= np.linalg.norm(upper_dir)
    if not isinstance(objects_to_sample_on, list):
        objects_to_sample_on = [objects_to_sample_on]

    if max_height < min_height:
        raise Exception("The minimum height ({}) must be smaller "
                        "than the maximum height ({})!".format(min_height, max_height))

    regions = []

    def calc_vec_and_normals(face: List[np.ndarray]) -> Tuple[Tuple[np.ndarray, np.ndarray], np.ndarray]:
        """ Calculates the two vectors, which lie in the plane of the face and the normal of the face.

        :param face: Four corner coordinates of a face. Type: [4x[3xfloat]].
        :return: (two vectors in the plane), and the normal.
        """
        vec1 = face[1] - face[0]
        vec2 = face[3] - face[0]
        normal = np.cross(vec1, vec2)
        normal = normal / np.linalg.norm(normal)
        return (vec1, vec2), normal

    # determine for each object in objects the region, where to sample on
    for obj in objects_to_sample_on:
        bb = obj.get_bound_box()
        faces = []
        faces.append([bb[0], bb[1], bb[2], bb[3]])
        faces.append([bb[0], bb[4], bb[5], bb[1]])
        faces.append([bb[1], bb[5], bb[6], bb[2]])
        faces.append([bb[6], bb[7], bb[3], bb[2]])
        faces.append([bb[3], bb[7], bb[4], bb[0]])
        faces.append([bb[7], bb[6], bb[5], bb[4]])
        # select the face, which has the smallest angle to the upper direction
        min_diff_angle = 2 * math.pi
        selected_face = None
        for face in faces:
            # calc the normal of all faces
            _, normal = calc_vec_and_normals(face)
            diff_angle = math.acos(normal.dot(upper_dir))
            if diff_angle < min_diff_angle:
                min_diff_angle = diff_angle
                selected_face = face
        # save the selected face values
        if selected_face is not None:
            vectors, normal = calc_vec_and_normals(selected_face)
            base_point = selected_face[0]
            regions.append(Region2D(vectors, normal, base_point))
        else:
            raise Exception("Couldn't find a face, for this obj: {}".format(obj.get_name()))

    if regions and len(regions) == len(objects_to_sample_on):
        selected_region_id = random.randint(0, len(regions) - 1)
        selected_region, obj = regions[selected_region_id], objects_to_sample_on[selected_region_id]
        if use_ray_trace_check:
            inv_world_matrix = np.linalg.inv(obj.get_local2world_mat())
        while True:
            ret = selected_region.sample_point(face_sample_range)
            dir = upper_dir if use_upper_dir else selected_region.normal()
            ret += dir * random.uniform(min_height, max_height)
            if use_ray_trace_check:
                # transform the coords into the reference frame of the object
                c_ret = inv_world_matrix @ ret
                c_dir = inv_world_matrix @ (dir * -1.0)
                # check if the object was hit
                hit, _, _, _ = obj.ray_cast(c_ret, c_dir)
                if hit:  # if the object was hit return
                    break
            else:
                break
        return np.array(ret)
    else:
        raise Exception("The amount of regions is either zero or does not match the amount of objects!")


class Region2D(object):
    """ Helper class for UpperRegionSampler: Defines a 2D region in 3D.
    """

    def __init__(self, vectors: Tuple[np.ndarray, np.ndarray], normal: np.ndarray, base_point: np.ndarray):
        self._vectors = vectors  # the two vectors which lie in the selected face
        self._normal = normal  # the normal of the selected face
        self._base_point = base_point  # the base point of the selected face

    def sample_point(self, face_sample_range: np.ndarray) -> np.ndarray:
        """
        Samples a point in the 2D Region

        :param face_sample_range: relative lengths of both face vectors between which points are sampled
        :return:
        """
        ret = self._base_point.copy()
        # walk over both vectors in the plane and determine a distance in both direction
        for vec in self._vectors:
            ret += vec * random.uniform(face_sample_range[0], face_sample_range[1])
        return ret

    def normal(self):
        """
        :return: the normal of the region
        """
        return self._normal
