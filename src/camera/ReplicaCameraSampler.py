import math
import random

import bpy
import mathutils
import numpy as np
import os
import ast

import bmesh

from src.camera.CameraModule import CameraModule


class ReplicaCameraSampler(CameraModule):

    def __init__(self, config):
        CameraModule.__init__(self, config)
        self.camera_height = 1.55 # out of the suncg scn2cam
        self.camera_height_radius = 0.05 # out of the suncg scn2cam, -0.05 - +0.05 on the camera height added
        self.camera_rotation_angle_x = 78.6901 # out of the suncg scn2cam
        self.position_ranges = [
            self.config.get_list("positon_range_x", []),
            self.config.get_list("positon_range_y", []),
            self.config.get_list("positon_range_z", [self.camera_height, self.camera_height])
        ]
        self.rotation_ranges = [
            self.config.get_list("rotation_range_x", [self.camera_rotation_angle_x, self.camera_rotation_angle_x]),
            self.config.get_list("rotation_range_y", [0, 0]),
            self.config.get_list("rotation_range_z", [])
        ]
        self.sqrt_number_of_rays = self.config.get_int("sqrt_number_of_rays", 10)
        self.min_dist_to_obstacle = self.config.get_float("min_dist_to_obstacle", 1)
        self.cams_per_square_meter = self.config.get_float("cams_per_square_meter", 0.5)
        self.max_tries_per_room = self.config.get_int("max_tries_per_room", 10000)
        self.number_of_successfull_tries = self.config.get_int('sample_amount', 25)
        self.bvh_tree = None

    def run(self):
        """ Samples multiple cameras per suncg room.

        Procedure per room:
         - sample position inside bbox
         - send ray from position straight down and make sure it hits the room's floor first
         - send rays through the field of view to approximate a depth map and to make sure no obstacle is too close to the camera
        """
        self._init_bvh_tree()

        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data
        cam.lens_unit = 'FOV'
        cam.angle = 1.0
        # cam.clip_start = self.config.get_float("near_clipping", 1)

        # Set resolution and aspect ratio, as they have an influence on the near plane
        bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", 512)
        bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", 512)
        bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1)

        frame_id = 0
        tries = 0
        successful_tries = 0
        print(self.number_of_successfull_tries)
        if 'mesh' in bpy.data.objects:
            bounding_box = bpy.data.objects['mesh'].bound_box
            bounding_box = {"min": bounding_box[0], "max": bounding_box[-2]}
        else:
            raise Exception("Mesh object is not defined!")
        if 'floor' in bpy.data.objects:
            floor_object = bpy.data.objects['floor']
        else:
            raise Exception("No floor object is defined!")

        file_path = self.config.get_string('height_list_path')
        with open(file_path) as file:
            height_list = [float(val) for val in ast.literal_eval(file.read())]
        while successful_tries < self.number_of_successfull_tries and tries < self.max_tries_per_room:
            tries += 1
            position = self._sample_position({"bbox" :bounding_box}, height_list)

            if not self._position_is_above_floor(position, floor_object):
                continue

            orientation = self._sample_orientation()
            # orientation = mathutils.Vector([math.radians(ele) for ele in [78.7, 0., 165.0]])

            # Compute the world matrix of a cam with the given pose
            world_matrix = mathutils.Matrix.Translation(mathutils.Vector(position)) @ mathutils.Euler(orientation, 'XYZ').to_matrix().to_4x4()

            if self._is_too_close_obstacle_in_view(cam, position, world_matrix):
                continue

            # Set the camera pose at the next frame:
            cam_ob.location = position
            cam_ob.rotation_euler = orientation
            cam_ob.keyframe_insert(data_path='location', frame=frame_id + 1)
            cam_ob.keyframe_insert(data_path='rotation_euler', frame=frame_id + 1)

            self._write_cam_pose_to_file(frame_id + 1, cam, cam_ob, suncg_version=True)
            print(tries, successful_tries)
            # break

            frame_id += 1
            successful_tries += 1

        print(str(tries) + " tries were necessary")

        bpy.context.scene.frame_end = frame_id
        self._register_cam_pose_output()

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

    def _calc_number_of_cams_in_room(self, room_obj):
        """ Approximates the square meters of the room and then uses cams_per_square_meter to get total number of cams in room.

        :param room_obj: The room object whose bbox will be used to approximate the size.
        :return: The number of camera positions planned for this room.
        """
        return math.floor(abs(room_obj["bbox"]["max"][0] - room_obj["bbox"]["min"][0]) * abs(room_obj["bbox"]["max"][1] - room_obj["bbox"]["min"][1]) * self.cams_per_square_meter)

    def _sample_position(self, room_obj, floor_height_values):
        """ Samples a random position inside the bbox of the given room object.

        :param room_obj: The room object whose bbox is used.
        :return: A vector describing the sampled position
        """
        position = mathutils.Vector()
        for i in range(2):
            # Check if a interval for sampling has been configured, otherwise sample inside bbox
            if len(self.position_ranges[i]) != 2:
                position[i] = random.uniform(room_obj["bbox"]["min"][i], room_obj["bbox"]["max"][i])
            else:
                position[i] = random.uniform(room_obj["bbox"]["min"][i] + self.position_ranges[i][0], room_obj["bbox"]["min"][i] + self.position_ranges[i][1])
        position[2] = floor_height_values[random.randrange(0, len(floor_height_values))] + self.camera_height
        return position

    def _position_is_above_floor(self, position, floor_obj):
        """ Make sure the given position is straight above the given floor object with no obstacles in between.

        :param position: The position to check.
        :return: True, if a ray sent into negative z-direction starting from the position hits the floor first.
        """
        # Send a ray straight down and check if the first hit object is the floor
        hit, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(bpy.context.view_layer, position, mathutils.Vector([0, 0, -1]))
        return hit and hit_object == floor_obj


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
        mean_value = 0
        mean_counter = 0
        for x in range(0, self.sqrt_number_of_rays):
            for y in range(0, self.sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / float(self.sqrt_number_of_rays - 1) + vec_y * y / float(self.sqrt_number_of_rays - 1)
                # Send ray from the camera position through the current point on the plane
                _, _, _, dist = self.bvh_tree.ray_cast(position, end - position, 4)

                # Check if something was hit and how far it is away
                if dist is not None:
                    if 1.0 < dist:
                        mean_value += dist
                        mean_counter += 1
                else:
                    print("is none")
                    return True
        print("Mean {}".format(mean_counter))
        if mean_counter == self.sqrt_number_of_rays * self.sqrt_number_of_rays:
            mean_value = mean_value / float(mean_counter)
            print("Mean val: {}, pos: {}".format(mean_value, position))
            if 2.0 <= mean_value <= 3.0:
                return False
        return True
