""" This module provides functionality to sample a spotlight, which intersects with the current camera frustum,
without being inside the camera frustum.
"""

from typing import Optional, Callable

import bpy
import numpy as np

from blenderproc.python.camera.CameraUtility import get_camera_frustum, is_point_inside_camera_frustum, \
    get_camera_pose, rotation_from_forward_vec
from blenderproc.python.sampler.PartSphere import part_sphere
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.types.MeshObjectUtility import create_bvh_tree_multi_objects, get_all_mesh_objects
from blenderproc.python.utility.Utility import KeyFrame


def _default_light_pose_sampling(frustum_vertices: np.ndarray) -> np.ndarray:
    """ Samples a new spotlight pose based on the camera frustum vertices.

    :param frustum_vertices: The eight 3D coordinates of the camera frustum
    :return: The newly sampled 3D spotlight pose
    """
    middle_frustum_point = np.mean(frustum_vertices, axis=0)
    cube_diag = np.linalg.norm(np.max(frustum_vertices, axis=0) - np.min(frustum_vertices, axis=0)) * 0.5
    sampled_light_pose = part_sphere(middle_frustum_point,
                                     radius=np.random.uniform(cube_diag * 0.01, cube_diag * 0.75), mode="SURFACE")
    return sampled_light_pose


def _default_look_at_pose_sampling(frustum_vertices: np.ndarray, _sampled_light_pose: np.ndarray) -> np.ndarray:
    """ This function samples the default look at location and is used inside
    the `add_intersecting_spot_lights_to_camera_poses`.

    :param frustum_vertices: The eight 3D coordinates of the camera frustum
    :param _sampled_light_pose: The currently sampled light pose
    :return: A new 3D look at pose
    """
    middle_frustum_point = np.mean(frustum_vertices, axis=0)
    return middle_frustum_point + np.random.normal(0, 1.0, 3)


def add_intersecting_spot_lights_to_camera_poses(clip_start: float, clip_end: float,
                                                 perform_look_at_intersection_check: bool = True,
                                                 perform_look_at_pose_visibility_check: bool = True,
                                                 light_pose_sampling: Optional[Callable[[np.ndarray],
                                                                                        np.ndarray]] = None,
                                                 look_at_pose_sampling: Optional[Callable[[np.ndarray, np.ndarray],
                                                                                          np.ndarray]] = None,
                                                 max_tries_per_cam_pose: int = 10000) -> Light:
    """ This functions adds spotlights which intersect with the camera pose. This is useful to get a greater variety
    in lighting situations then the general full illumination from all sides.

    The spotlights location is defined by the `light_pose_sampling` parameter, it gets the eight coordinates of the
    camera frustum vertices. This camera frustum starts at `clip_start` and ends at `clip_end`. It should return a
    single 3D point. This point is then checked to not be in the camera frustum, if it is inside a new point will be
    sampled.

    After the defining a suitable light position, a look at pose is sampled via the `look_pose_sampling` function.
    It uses the same eight coordinates of the camera frustum and the current sampled light position to return a look at
    pose.

    If the `perform_look_at_intersection_check` value is set an intersection check between the light position and
    the look at location is done, which ensures that no object is between these two points.
    Similarly, for the `perform_look_at_pose_visibility_check`, a newly sampled light pose does not have an intersecting
    object between this sampled pose and the camera location.

    :param clip_start: The distance between the camera pose and the near clipping plane, used for the sampling of a
                       light and look at location
    :param clip_end: The distance between the camera pose and the far clipping plane, used for the sampling of a
                     light and look at location
    :param perform_look_at_intersection_check: If this is True an intersection check between the light pose and the look
                                               at pose is done, if an object is inbetween both poses are discarded.
    :param perform_look_at_pose_visibility_check: If this is True, an intersection check between the look at pose and
                                                  the camera location is done, to ensure that the light is visible and
                                                  not hidden.
    :param light_pose_sampling: This function samples a new 3D light pose based on the eight 3D coordinates of the
                                camera frustum. If this is None, the `_default_light_pose_sampling` is used.
    :param look_at_pose_sampling: This function samples a new 3D look at pose based on the eight 3D coordinates of the
                                  camera frustum and the currently sampled light pose. If this is None,
                                  the `_default_look_at_pose_sampling` is used.
    :param max_tries_per_cam_pose: The amount of maximum tries per camera pose for finding a new light pose with
                                   look at pose.
    :return: The newly generated light
    """

    if bpy.context.scene.frame_start == bpy.context.scene.frame_end:
        raise RuntimeError("A camera poses has to be set first!")

    if light_pose_sampling is None:
        light_pose_sampling = _default_light_pose_sampling

    if look_at_pose_sampling is None:
        look_at_pose_sampling = _default_look_at_pose_sampling

    new_light = Light(light_type="SPOT")
    new_light.set_energy(10000)
    # create a bvh tree to quickly check if an object is in the line of sight
    bvh_tree = None
    if perform_look_at_pose_visibility_check or perform_look_at_intersection_check:
        bvh_tree = create_bvh_tree_multi_objects(get_all_mesh_objects())

    # iterate over each camera pose
    for frame_id in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
        # set the current camera frame for all functions
        with KeyFrame(frame_id):
            # get the vertices of the camera frustum
            vertices = get_camera_frustum(clip_start=clip_start, clip_end=clip_end)
            found_pose = False
            for _ in range(max_tries_per_cam_pose):
                # sample a new light position
                sampled_pose = light_pose_sampling(vertices)
                # sample a look at pose
                look_at_point = look_at_pose_sampling(vertices, sampled_pose)
                # check that the sampled pose is not inside the camera frustum and the look at point is
                if not is_point_inside_camera_frustum(sampled_pose) and is_point_inside_camera_frustum(look_at_point):
                    # check if an object is between the look at pose and the camera pose
                    if perform_look_at_pose_visibility_check:
                        cam_location = get_camera_pose()[:3, 3]
                        look_dir = cam_location - look_at_point
                        _, _, _, dist = bvh_tree.ray_cast(look_at_point, look_dir, np.linalg.norm(look_dir))
                        if dist is not None:
                            # if an object is between the light pose and the camera sample a new light pose
                            continue
                    # check if an object is between the sample point and the look at point
                    if perform_look_at_intersection_check:
                        look_dir = look_at_point - sampled_pose
                        _, _, _, dist = bvh_tree.ray_cast(sampled_pose, look_dir, np.linalg.norm(look_dir))
                        if dist is not None:
                            # skip this light position as it collides with something
                            continue

                    # calculate the rotation matrix
                    forward_vec = look_at_point - sampled_pose
                    rotation_matrix = rotation_from_forward_vec(forward_vec)

                    # save the pose and rotation
                    new_light.set_location(sampled_pose)
                    new_light.set_rotation_mat(rotation_matrix)
                    found_pose = True
                    break
            if not found_pose:
                raise RuntimeError("No pose found, increase the start and end clip or increase the amount of tries.")
    return new_light
