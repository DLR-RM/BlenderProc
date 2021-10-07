import random
from typing import List

import numpy as np

from blenderproc.python.types.MeshObjectUtility import MeshObject


class Front3DPointInRoomSampler:

    def __init__(self, front3d_objects: List[MeshObject], amount_of_objects_needed_per_room: int = 2):
        """ Collects the floors of all rooms with at least N objects.

        :param front3d_objects: The list of front3d objects that should be considered.
        :param amount_of_objects_needed_per_room: The number of objects a rooms needs to have, such that it is considered for sampling.
        """
        front3d_objects = [obj for obj in front3d_objects if obj.has_cp("is_3D_future")]

        floor_objs = [obj for obj in front3d_objects if obj.get_name().lower().startswith("floor")]

        # count objects per floor -> room
        floor_obj_counters = {obj.get_name(): 0 for obj in floor_objs}
        counter = 0
        for obj in front3d_objects:
            name = obj.get_name().lower()
            if "wall" in name or "ceiling" in name:
                continue
            counter += 1

            for floor_obj in floor_objs:
                is_above = floor_obj.position_is_above_object(obj.get_location())
                if is_above:
                    floor_obj_counters[floor_obj.get_name()] += 1
        self.used_floors = [obj for obj in floor_objs if floor_obj_counters[obj.get_name()] > amount_of_objects_needed_per_room]


    def sample(self, height: float, max_tries: int = 1000) -> np.ndarray:
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
            bounding_box = floor_obj.get_bound_box()
            min_corner = np.min(bounding_box, axis=0)
            max_corner = np.max(bounding_box, axis=0)

            # Sample uniformly inside bounding box
            point = np.array([
                random.uniform(min_corner[0], max_corner[0]),
                random.uniform(min_corner[1], max_corner[1]),
                floor_obj.get_location()[2] + height
            ])

            # Check if sampled pose is above the floor to make sure its really inside the room
            if floor_obj.position_is_above_object(point):
                return point

        raise Exception("Cannot sample any point inside the loaded front3d rooms.")
