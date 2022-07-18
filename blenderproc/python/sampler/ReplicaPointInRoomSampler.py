import ast
from typing import Union, List, Dict
import random
import numpy as np

from blenderproc.python.types.MeshObjectUtility import MeshObject


class ReplicaPointInRoomSampler:

    def __init__(self, room_bounding_box: Dict[str, np.ndarray], replica_floor: Union[MeshObject, List[MeshObject]],
                 height_list_file_path: str):
        """ Collect object containing all floors of all rooms and read in text file containing possible height values.

        :param room_bounding_box: The bounding box of the room, needs a min key and max key, representing the edges of
                                  the room bounding box
        :param replica_floor: The replica floor object.
        :param height_list_file_path: The path to the file containing possible height values.
        """
        self.bounding_box = room_bounding_box
        self.floor_object = replica_floor
        if isinstance(self.floor_object, list) and not self.floor_object:
            raise Exception("The floor object list can not be empty!")

        with open(height_list_file_path) as file:
            self.floor_height_values = [float(val) for val in ast.literal_eval(file.read())]

    def sample(self, height: float, max_tries: int = 1000) -> np.ndarray:
        """ Samples a point inside one of the loaded replica rooms.

        The points are uniformly sampled along x/y over all rooms.
        The z-coordinate is set based on the given height value.

        :param height: The height above the floor to use for the z-component of the point.
        :param max_tries: The maximum number of times sampling above the floor should be tried.
        :return: The sampled point.
        """
        for _ in range(max_tries):

            # Sample uniformly inside bounding box
            point = np.array([
                random.uniform(self.bounding_box["min"][0], self.bounding_box["max"][0]),
                random.uniform(self.bounding_box["min"][1], self.bounding_box["max"][1]),
                self.floor_height_values[random.randrange(0, len(self.floor_height_values))] + height
            ])

            if isinstance(self.floor_object, list):
                for floor_object in self.floor_object:
                    # Check if sampled pose is above the floor to make sure it is really inside the room
                    if floor_object.position_is_above_object(point):
                        return point
            else:
                # Check if sampled pose is above the floor to make sure it is really inside the room
                if self.floor_object.position_is_above_object(point):
                    return point

        raise Exception("Cannot sample any point inside the loaded replica rooms.")
