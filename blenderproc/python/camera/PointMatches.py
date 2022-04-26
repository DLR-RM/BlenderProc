import numpy as np
from blenderproc.python.camera import CameraUtility
import bpy
from mathutils import Matrix

def compute_matches(point_clouds, cam_extrinsics):
    point_clouds = np.stack(point_clouds)
    point_clouds = np.concatenate((point_clouds, np.ones_like(point_clouds[...,:1])), -1)

    # Reproject using K matrix
    K = CameraUtility.get_intrinsics_as_K_matrix()
    # Account for different coordinate system in opencv and blender
    K[1][2] = (bpy.context.scene.render.resolution_x - 1) - K[1][2]
    K = np.array(K)
    for i, (cam_extrinsic, cam_location) in enumerate(cam_extrinsics):
        print(i)

        local_point_clouds = np.concatenate((point_clouds[:i], point_clouds[i+1:]),0)
        local_point_clouds = np.matmul(cam_extrinsic[None, None],  np.transpose(local_point_clouds, (0,1,3,2)))
        local_point_clouds = np.transpose(local_point_clouds, (0,1,3,2))

        local_point_clouds[...,2] *= -1
        # Reproject 3d point

        point_2d = np.matmul(K[None, None], np.transpose(local_point_clouds[..., :3], (0,1,3,2)))
        point_2d = np.transpose(point_2d, (0, 1, 3, 2))
        point_2d /= point_2d[...,2:]
        point_2d = point_2d[...,:2]

        point_2d[..., 1] = (bpy.context.scene.render.resolution_x - 1) - point_2d[..., 1]

        point_2d[(point_2d < 0 - 1e-3).any(-1)] = np.nan
        point_2d[(point_2d > (bpy.context.scene.render.resolution_x - 1) + 1e-3).any(-1)] = np.nan

        own_depth = np.linalg.norm(point_clouds[i,...,:3] - cam_location[None, None], axis=-1)
        print("a")
        local_point_clouds = np.concatenate((point_clouds[:i], point_clouds[i+1:]),0)
        repr_depth = np.linalg.norm(local_point_clouds[..., :3] - cam_location[None, None, None], axis=-1)
        repr_point = np.round(point_2d).astype(np.int)
        repr_point[np.isnan(point_2d)] = 0

        own_depth = own_depth[repr_point[..., 1], repr_point[..., 0]]
        point_2d[np.abs(own_depth - repr_depth) > 1e-2] = np.nan

        return point_2d


def compute_point_cloud( cam2world_matrix, bvh_tree_target, bvh_tree_other):
    """ Check if there is an obstacle in front of the camera which is less than the configured
        "min_dist_to_obstacle" away from it.

    :param cam: The camera whose view frame is used (only FOV is relevant, pose of cam is ignored).
    :param cam2world_matrix: Transformation matrix that transforms from the camera space to the world space.
    :return: True, if there are no obstacles too close to the cam.
    """
    cam2world_matrix = Matrix(cam2world_matrix)

    cam_ob = bpy.context.scene.camera
    cam = cam_ob.data

    # Get position of the corners of the near plane
    frame = cam.view_frame(scene=bpy.context.scene)
    # Bring to world space
    frame = [cam2world_matrix @ v for v in frame]

    # Compute vectors along both sides of the plane
    vec_x = frame[1] - frame[0]
    vec_y = frame[3] - frame[0]

    points = []
    sqrt_number_of_rays = bpy.context.scene.render.resolution_x
    # Go in discrete grid-like steps over plane
    position = cam2world_matrix.to_translation()
    for x in range(0, sqrt_number_of_rays):
        for y in reversed(range(0, sqrt_number_of_rays)):
            # Compute current point on plane
            end = frame[0] + vec_x * (x + 0.5) / float(sqrt_number_of_rays) \
                  + vec_y * (y + 0.5) / float(sqrt_number_of_rays)
            # Send ray from the camera position through the current point on the plane
            _, _, _, dist_target = bvh_tree_target.ray_cast(position, end - position)
            _, _, _, dist_obstacle = bvh_tree_other.ray_cast(position, end - position)

            if dist_target is not None and (dist_obstacle is None or dist_target <= dist_obstacle):
                dist = dist_target
            else:
                dist = np.nan

            point = position + dist * (end - position).normalized()
            points.append(point)

    points = np.array(points)
    points = np.reshape(points, [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y, 3])
    #points = np.reshape(points, [512, 512, 3])
    return points
