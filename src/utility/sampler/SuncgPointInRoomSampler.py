import random

import bpy

from src.utility.camera.CameraValidation import CameraValidation
from mathutils import Vector

class SuncgPointInRoomSampler:

    def __init__(self):
        # Collect all valid room objects
        self.rooms = []
        for room_obj in bpy.context.scene.objects:
            # Check if object is from type room and has bbox
            if "type" in room_obj and room_obj["type"] == "Room" and "bbox" in room_obj:

                # Make sure the room has a floor which is required for sampling
                floor_obj = self._find_floor(room_obj)
                if floor_obj is not None:
                    self.rooms.append((room_obj, floor_obj))

    def sample(self, height: float, max_tries: int = 1000) -> Vector:
        """ Samples a point inside one of the loaded suncg rooms.

        The points are uniformly sampled along x/y over all rooms.
        The z-coordinate is set based on the given height value.

        :param height: The height above the floor to use for the z-component of the point.
        :param max_tries: The maximum number of times sampling above the floor should be tried.
        :return: The sampled point.
        """
        for _ in range(max_tries):
            # Sample room
            room_id = random.randrange(len(self.rooms))
            room_obj, floor_obj = self.rooms[room_id]

            point = Vector([
                random.uniform(room_obj["bbox"]["min"][0], room_obj["bbox"]["max"][0]),
                random.uniform(room_obj["bbox"]["min"][1], room_obj["bbox"]["max"][1]),
                room_obj["bbox"]["min"][2] + height
            ])

            # Check if sampled pose is valid
            if CameraValidation.position_is_above_object(point, floor_obj):
                return point

        raise Exception("Cannot sample any point inside the loaded suncg rooms.")

    def _find_floor(self, room_obj: bpy.types.Object) -> bpy.types.Object:
        """ Returns the floor object of the given room object.

        Goes through all children and returns the first one with type "Floor".

        :param room_obj: The room object.
        :return: The found floor object or None if none has been found.
        """
        for obj in bpy.context.scene.objects:
            if obj.parent == room_obj and "type" in obj and obj["type"] == "Floor":
                return obj
        return None
