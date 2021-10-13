import random
from typing import Tuple, List, Optional
import numpy as np

from blenderproc.python.types.MeshObjectUtility import MeshObject


class SuncgPointInRoomSampler:

    def __init__(self, suncg_objects: List[MeshObject]):
        """
        :param suncg_objects: The list of suncg objects to consider.
        """
        # Collect all valid room objects
        self.rooms = []
        for room_obj in suncg_objects:
            # Check if object is from type room and has bbox
            if room_obj.has_cp("type") and room_obj.get_cp("type") == "Room" and room_obj.has_cp("bbox"):

                # Make sure the room has a floor which is required for sampling
                floor_obj = self._find_floor(suncg_objects, room_obj)
                if floor_obj is not None:
                    self.rooms.append((room_obj, floor_obj))

    def sample(self, height: float, max_tries: int = 1000) -> Tuple[np.ndarray, int]:
        """ Samples a point inside one of the loaded suncg rooms.

        The points are uniformly sampled along x/y over all rooms.
        The z-coordinate is set based on the given height value.

        :param height: The height above the floor to use for the z-component of the point.
        :param max_tries: The maximum number of times sampling above the floor should be tried.
        :return: The sampled point and the id of the room it was sampled in.
        """
        for _ in range(max_tries):
            # Sample room
            room_id = random.randrange(len(self.rooms))
            room_obj, floor_obj = self.rooms[room_id]

            point = np.array([
                random.uniform(room_obj.get_cp("bbox")["min"][0], room_obj.get_cp("bbox")["max"][0]),
                random.uniform(room_obj.get_cp("bbox")["min"][1], room_obj.get_cp("bbox")["max"][1]),
                room_obj.get_cp("bbox")["min"][2] + height
            ])

            # Check if sampled pose is valid
            if floor_obj.position_is_above_object(point):
                return point, room_id

        raise Exception("Cannot sample any point inside the loaded suncg rooms.")

    def _find_floor(self, suncg_objects: List[MeshObject], room_obj: MeshObject) -> Optional[MeshObject]:
        """ Returns the floor object of the given room object.

        Goes through all children and returns the first one with type "Floor".

        :param suncg_objects:
        :param room_obj: The room object.
        :return: The found floor object or None if none has been found.
        """
        for obj in suncg_objects:
            if obj.get_parent() == room_obj and obj.has_cp("type") and obj.get_cp("type") == "Floor":
                return obj
        return None
