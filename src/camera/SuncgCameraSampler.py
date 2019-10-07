import math

import bpy
import mathutils

from src.camera.CameraSampler import CameraSampler
from src.utility.BoundingBoxSampler import BoundingBoxSampler

class SuncgCameraSampler(CameraSampler):

    def __init__(self, config):
        CameraSampler.__init__(self, config)
        self.cams_per_square_meter = self.config.get_float("cams_per_square_meter", 0.5)
        self.max_tries_per_room = self.config.get_int("max_tries_per_room", 10000)

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

        max = mathutils.Vector()
        min = mathutils.Vector()
        for i in range(3):
            # Check if an interval for sampling has been configured, otherwise sample inside bbox
            if len(self.position_ranges[i]) != 2:
                min[i] = room_obj["bbox"]["min"][i]
                max[i] = room_obj["bbox"]["max"][i]
            else:
                min[i] = room_obj["bbox"]["min"][i] + self.position_ranges[i][0]
                max[i] = room_obj["bbox"]["min"][i] + self.position_ranges[i][1]

        return BoundingBoxSampler.sample(min, max)


    def _calc_number_of_cams_in_room(self, room_obj):
        """ Approximates the square meters of the room and then uses cams_per_square_meter to get total number of cams in room.

        :param room_obj: The room object whose bbox will be used to approximate the size.
        :return: The number of camera positions planned for this room.
        """
        return math.floor(abs(room_obj["bbox"]["max"][0] - room_obj["bbox"]["min"][0]) * abs(room_obj["bbox"]["max"][1] - room_obj["bbox"]["min"][1]) * self.cams_per_square_meter)

    def _find_floor(self, room_obj):
        """ Returns the floor object of the given room object.

        Goes through all children and returns the first one with type "Floor".

        :param room_obj: The room object.
        :return: The found floor object or None if none has been found.
        """
        for obj in bpy.context.scene.objects:
            if obj.parent == room_obj and "type" in obj and obj["type"] == "Floor":
                return obj
        return None

    def _position_is_above_floor(self, position, floor_obj):
        """ Make sure the given position is straight above the given floor object with no obstacles in between.

        :param position: The position to check.
        :param floor_obj: The floor object to use.
        :return: True, if a ray sent into negative z-direction starting from the position hits the floor first.
        """

        return self._position_is_above_object(position, floor_obj)