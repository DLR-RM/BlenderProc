from src.camera.CameraModule import CameraModule
import mathutils
import bpy
import bmesh
import math
import random
import numpy as np
import os

class CameraSampler(CameraModule):

    """
    General class for a camera sampler. All common methods, attributes and initializations should be put here.
    """

    def __init__(self, config):
        CameraModule.__init__(self, config)

        self.position_ranges = [
            self.config.get_list("positon_range_x", []),
            self.config.get_list("positon_range_y", []),
            self.config.get_list("positon_range_z", [1.4, 1.4])
        ]
        self.rotation_ranges = [
            self.config.get_list("rotation_range_x", [90, 90]),
            self.config.get_list("rotation_range_y", [0, 0]),
            self.config.get_list("rotation_range_z", [])
        ]
        self.sqrt_number_of_rays = self.config.get_int("sqrt_number_of_rays", 10)
        self.min_dist_to_obstacle = self.config.get_float("min_dist_to_obstacle", 1)
        self.bvh_tree = None

    def _init_bvh_tree(self):
        """ Creates a bvh tree which contains all mesh objects in the scene.

        Such a tree is later used for fast raycasting.
        """
        # Create bmesh which will contain the meshes of all objects
        bm = bmesh.new()
        # Go through all mesh objects
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                # Add object mesh to bmesh (the newly added vertices will be automatically selected)
                bm.from_mesh(obj.data)
                # Apply world matrix to all selected vertices
                bm.transform(obj.matrix_world, filter={"SELECT"})
                # Deselect all vertices
                for v in bm.verts:
                    v.select = False

        # Create tree from bmesh
        self.bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

    def _sample_position(self, environment_object):
        raise NotImplementedError("Please Implement this method")


    def _position_is_above_object(self, position, object):
        """ Make sure the given position is straight above the given object with no obstacles in between.

        :param position: The position to check.
        :param object: The query object to use.
        :return: True, if a ray sent into negative z-direction starting from the position hits the object first.
        """
        # Send a ray straight down and check if the first hit object is the query object
        hit, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(bpy.context.view_layer, position, mathutils.Vector([0, 0, -1]))
        return hit and hit_object == object

    def _sample_orientation(self):
        """ Samples an orientation.

        :return: A vector which contains three euler angles describing the orientation.
        """
        orientation = mathutils.Vector()
        for i in range(3):
            # Check if a interval for sampling has been configured, otherwise use [0, 360]
            if len(self.rotation_ranges[i]) != 2:
                orientation[i] = random.uniform(0, math.pi * 2)
            else:
                orientation[i] = math.radians(random.uniform(self.rotation_ranges[i][0], self.rotation_ranges[i][1]))

        return orientation

    def _is_too_close_obstacle_in_view(self, cam, position, world_matrix):
        """ Check if there is an obstacle in front of the camera which is less than the configured "min_dist_to_obstacle" away from it.

        :param cam: The camera whose view frame is used (only FOV is relevant, pose of cam is ignored).
        :param position: The camera position vector to check
        :param world_matrix: The world matrix which describes the camera orientation to check.
        :return: True, if there is an obstacle to close too the cam.
        """
        # Get position of the corners of the near plane
        frame = cam.view_frame(scene=bpy.context.scene)
        # Bring to world space
        frame = [world_matrix @ v for v in frame]

        # Compute vectors along both sides of the plane
        vec_x = frame[1] - frame[0]
        vec_y = frame[3] - frame[0]

        # Go in discrete grid-like steps over plane
        for x in range(0, self.sqrt_number_of_rays):
            for y in range(0, self.sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / (self.sqrt_number_of_rays - 1) + vec_y * y / (self.sqrt_number_of_rays - 1)
                # Send ray from the camera position through the current point on the plane
                _, _, _, dist = self.bvh_tree.ray_cast(position, end - position, self.min_dist_to_obstacle)

                # Check if something was hit and how far it is away
                if dist is not None and dist <= self.min_dist_to_obstacle:
                    return True

        return False
