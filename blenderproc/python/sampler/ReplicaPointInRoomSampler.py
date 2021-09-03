import ast
import random
import numpy as np

from blenderproc.python.types.MeshObjectUtility import MeshObject


class ReplicaPointInRoomSampler:

    def __init__(self, replica_mesh: MeshObject, replica_floor: MeshObject, height_list_file_path: str):
        """ Collect object containing all floors of all rooms and read in text file containing possible height values.

        :param replica_mesh: The replica mesh object.
        :param replica_floor: The replica floor object.
        :param height_list_file_path: The path to the file containing possible height values.
        """
        # Determine bounding box of the scene
        bounding_box = replica_mesh.get_bound_box()
        self.bounding_box = {"min": bounding_box[0], "max": bounding_box[-2]}
        self.floor_object = replica_floor

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

            # Check if sampled pose is above the floor to make sure its really inside the room
            if self.floor_object.position_is_above_object(point):
                return point

        raise Exception("Cannot sample any point inside the loaded replica rooms.")
