import math
import random

import bpy
import mathutils
import numpy as np
import os

import bmesh

from src.camera import CameraSampler
from src.camera import BoundingBoxSampler

class SuncgCameraSampler(CameraSampler):

    def __init__(self, config):
        CameraSampler.__init__(self, config)

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

        # Set resolution and aspect ratio, as they have an influence on the near plane
        bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", 512)
        bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", 512)
        bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1)

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
                    world_matrix = mathutils.Matrix.Translation(mathutils.Vector(position)) @ mathutils.Euler(orientation, 'XYZ').to_matrix().to_4x4()

                    if self._is_too_close_obstacle_in_view(cam, position, world_matrix):
                        continue

                    # Set the camera pose at the next frame
                    cam_ob.location = position
                    cam_ob.rotation_euler = orientation
                    cam_ob.keyframe_insert(data_path='location', frame=frame_id + 1)
                    cam_ob.keyframe_insert(data_path='rotation_euler', frame=frame_id + 1)

                    self._write_cam_pose_to_file(frame_id + 1, cam, cam_ob, room_id)

                    frame_id += 1
                    successful_tries += 1

                print(str(tries) + " tries were necessary")
                room_id += 1

        bpy.context.scene.frame_end = frame_id
        self._register_cam_pose_output()


    def _sample_position(self, room_obj):
        """ Samples a random position inside the bbox of the given room object.

        :param room_obj: The room object whose bbox is used.
        :return: A vector describing the sampled position
        """
        return BoundingBoxSampler.sample(room_obj["bbox"]["min"], room_obj["bbox"]["max"], self.position_ranges)

