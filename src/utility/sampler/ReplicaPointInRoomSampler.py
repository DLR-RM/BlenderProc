import ast
import os
import random

import bpy

from src.camera.CameraSampler import CameraSampler
from src.utility.CameraUtility import CameraUtility
from src.utility.Config import Config
from src.utility.Utility import Utility
from src.utility.camera.CameraValidation import CameraValidation
from mathutils import Vector

class ReplicaPointInRoomSampler:

    def __init__(self, height_list_file_path: str):
        """ Collect object containing all floors of all rooms and read in text file containing possible height values.

        :param height_list_file_path: The path to the file containing possible height values.
        """
        # Determine bounding box of the scene
        if 'mesh' in bpy.data.objects:
            bounding_box = bpy.data.objects['mesh'].bound_box
            self.bounding_box = {"min": bounding_box[0], "max": bounding_box[-2]}
        else:
            raise Exception("Mesh object is not defined!")

        # Find floor object
        if 'floor' in bpy.data.objects:
            self.floor_object = bpy.data.objects['floor']
        else:
            raise Exception("No floor object is defined!")

        with open(height_list_file_path) as file:
            self.floor_height_values = [float(val) for val in ast.literal_eval(file.read())]

    def sample(self, height: float, max_tries: int = 1000) -> Vector:
        """ Samples a point inside one of the loaded replica rooms.

        The points are uniformly sampled along x/y over all rooms.
        The z-coordinate is set based on the given height value.

        :param height: The height above the floor to use for the z-component of the point.
        :param max_tries: The maximum number of times sampling above the floor should be tried.
        :return: The sampled point.
        """
        for _ in range(max_tries):

            # Sample uniformly inside bounding box
            point = Vector([
                random.uniform(self.bounding_box["min"][0], self.bounding_box["max"][0]),
                random.uniform(self.bounding_box["min"][1], self.bounding_box["max"][1]),
                self.floor_height_values[random.randrange(0, len(self.floor_height_values))] + height
            ])

            # Check if sampled pose is above the floor to make sure its really inside the room
            if CameraValidation.position_is_above_object(point, self.floor_object):
                return point

        raise Exception("Cannot sample any point inside the loaded replica rooms.")
