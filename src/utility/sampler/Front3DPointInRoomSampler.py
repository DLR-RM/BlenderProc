import random

import numpy as np
from mathutils import Vector

from src.utility.BlenderUtility import get_all_blender_mesh_objects, get_bounds
from src.utility.camera.CameraValidation import CameraValidation


class Front3DPointInRoomSampler:

    def __init__(self, amount_of_objects_needed_per_room: int = 2):
        """ Collects the floors of all rooms with at least N objects.

        :param amount_of_objects_needed_per_room: The number of objects a rooms needs to have, such that it is considered for sampling.
        """
        all_objects = get_all_blender_mesh_objects()
        front_3D_objs = [obj for obj in all_objects if "is_3D_future" in obj and obj["is_3D_future"]]

        floor_objs = [obj for obj in front_3D_objs if obj.name.lower().startswith("floor")]

        # count objects per floor -> room
        floor_obj_counters = {obj.name: 0 for obj in floor_objs}
        counter = 0
        for obj in front_3D_objs:
            name = obj.name.lower()
            if "wall" in name or "ceiling" in name:
                continue
            counter += 1
            location = obj.location
            for floor_obj in floor_objs:
                is_above = CameraValidation.position_is_above_object(location, floor_obj)
                if is_above:
                    floor_obj_counters[floor_obj.name] += 1
        self.used_floors = [obj for obj in floor_objs if floor_obj_counters[obj.name] > amount_of_objects_needed_per_room]


    def sample(self, height: float, max_tries: int = 1000) -> Vector:
        """ Samples a point inside one of the loaded Front3d rooms.

        The points are uniformly sampled along x/y over all rooms.
        The z-coordinate is set based on the given height value.

        :param height: The height above the floor to use for the z-component of the point.
        :param max_tries: The maximum number of times sampling above the floor should be tried.
        :return: The sampled point.
        """
        for _ in range(max_tries):
            # Sample room via floor objects
            floor_obj = random.choice(self.used_floors)

            # Get min/max along x/y-axis from bounding box of room
            bounding_box = get_bounds(floor_obj)
            min_corner = np.min(bounding_box, axis=0)
            max_corner = np.max(bounding_box, axis=0)

            # Sample uniformly inside bounding box
            point = Vector([
                random.uniform(min_corner[0], max_corner[0]),
                random.uniform(min_corner[1], max_corner[1]),
                floor_obj.location[2] + height
            ])

            # Check if sampled pose is above the floor to make sure its really inside the room
            if CameraValidation.position_is_above_object(point, floor_obj):
                return point

        raise Exception("Cannot sample any point inside the loaded front3d rooms.")
