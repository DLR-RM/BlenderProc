import math
import random

import bpy
import mathutils
import numpy as np
import os

from src.main.Module import Module
import bmesh

from src.utility.Utility import Utility


class SuncgCameraSampler(Module):

    def __init__(self, config):
        Module.__init__(self, config)
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
        self.cams_per_square_meter = self.config.get_float("cams_per_square_meter", 0.5)
        self.max_tries_per_room = self.config.get_int("max_tries_per_room", 10000)
        self.write_to_file = self.config.get_bool("write_to_file", False)
        self.bvh_tree = None

    def run(self):
        self._init_bvh_tree()

        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        # Set resolution and aspect ratio, as they have an influence on the near plane
        bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", 512)
        bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", 512)
        bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1)

        cam_poses = []
        frame_id = 0
        room_id = 0
        for room_obj in bpy.context.scene.objects:
            # Find room objects
            if "type" in room_obj and room_obj["type"] == "Room" and "bbox" in room_obj:

                floor_obj = self._find_floor(room_obj)
                if floor_obj is None:
                    continue

                number_of_cams = self._calc_number_of_cams_in_room(room_obj)
                print("Generating " + str(number_of_cams) + " cams for room " + room_obj.name + " (" + str(room_obj["roomTypes"]) + ")")

                # Now try to generate the requested number of cams
                successful_tries = 0
                tries = 0
                while successful_tries < number_of_cams and tries < self.max_tries_per_room:
                    tries += 1
                    position = self._sample_position(room_obj)

                    if not self._position_is_above_floor(position, floor_obj):
                        continue

                    orientation = self._sample_orientation()

                    # Compute the world matrix of a cam with the given pose
                    world_matrix = mathutils.Matrix.Translation(mathutils.Vector(position)) * mathutils.Euler(orientation, 'XYZ').to_matrix().to_4x4()

                    if self._is_too_close_obstacle_in_view(cam, position, world_matrix):
                        continue

                    # Set the camera pose at the next frame
                    cam_ob.location = position
                    cam_ob.rotation_euler = orientation
                    cam_ob.keyframe_insert(data_path='location', frame=frame_id + 1)
                    cam_ob.keyframe_insert(data_path='rotation_euler', frame=frame_id + 1)

                    if self.write_to_file:
                        cam_poses.append([])
                        # Eye vector
                        cam_poses[-1].extend(position[:])
                        # Look at vector
                        cam_poses[-1].extend((world_matrix.to_quaternion() * mathutils.Vector((0.0, 0.0, -1.0)))[:])
                        # Up vector
                        cam_poses[-1].extend((world_matrix.to_quaternion() * mathutils.Vector((0.0, 1.0, 0.0)))[:])
                        # FOV and Room
                        cam_poses[-1].extend([cam.angle_x, cam.angle_y, room_id])

                    frame_id += 1
                    successful_tries += 1

                print(str(tries) + " tries were necessary")
                room_id += 1

        bpy.context.scene.frame_end = frame_id
        if self.write_to_file:
            self._write_cam_poses_to_file(cam_poses)
            self._register_output("campose_", "campose", ".npy")

    def _write_cam_poses_to_file(self, cam_poses):
        for i, cam_pose in enumerate(cam_poses):
            np.save(os.path.join(self.output_dir, "campose_" + ("%04d" % (i + 1))), cam_pose)

    def _init_bvh_tree(self):
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
        """ Approximates the square meters of the room and then uses cams_per_square_meter to get total number of cams in room. """
        return math.floor(abs(room_obj["bbox"]["max"][0] - room_obj["bbox"]["min"][0]) * abs(room_obj["bbox"]["max"][1] - room_obj["bbox"]["min"][1]) * self.cams_per_square_meter)

    def _find_floor(self, room_obj):
        for obj in bpy.context.scene.objects:
            if obj.parent == room_obj and "type" in obj and obj["type"] == "Floor":
                return obj
        return None

    def _sample_position(self, room_obj):
        position = mathutils.Vector()
        for i in range(3):
            # Check if a interval for sampling has been configured, otherwise sample inside bbox
            if len(self.position_ranges[i]) != 2:
                position[i] = random.uniform(room_obj["bbox"]["min"][i], room_obj["bbox"]["max"][i])
            else:
                position[i] = random.uniform(self.position_ranges[i][0], self.position_ranges[i][1])

        return position

    def _position_is_above_floor(self, position, floor_obj):
        # Send a ray straight down and check if the first hit object is the floor
        hit, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(position, mathutils.Vector([0, 0, -1]))
        return hit and hit_object == floor_obj

    def _sample_orientation(self):
        orientation = mathutils.Vector()
        for i in range(3):
            # Check if a interval for sampling has been configured, otherwise use [0, 360]
            if len(self.rotation_ranges[i]) != 2:
                orientation[i] = random.uniform(0, math.pi * 2)
            else:
                orientation[i] = math.radians(random.uniform(self.rotation_ranges[i][0], self.rotation_ranges[i][1]))

        return orientation

    def _is_too_close_obstacle_in_view(self, cam, position, world_matrix):

        # Get position of the corners of the near plane
        frame = cam.view_frame(scene=bpy.context.scene)
        # Bring to world space
        frame = [world_matrix * v for v in frame]

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
