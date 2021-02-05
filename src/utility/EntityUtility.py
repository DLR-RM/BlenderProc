from typing import Union

import bpy
from src.utility.Utility import Utility, KeyFrame
from mathutils import Vector, Euler, Color

class Entity(object):

    def __init__(self, object: bpy.types.Object):
        self.blender_obj = object

    @staticmethod
    def convert_to_entities(blender_objects: list):
        return [Entity(obj) for obj in blender_objects]

    def set_location(self, location: Union[list, Vector], frame: int = None):
        """ Sets the location of the light in 3D world coordinates.

        :param location: The location to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.location = location
        Utility.insert_keyframe(self.blender_obj, "location", frame)

    def set_rotation_euler(self, rotation_euler: Union[list, Euler], frame: int = None):
        """ Sets the rotation of the light in euler angles.

        :param rotation_euler: The euler angles to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.rotation_euler = rotation_euler
        Utility.insert_keyframe(self.blender_obj, "rotation_euler", frame)

    def get_location(self, frame: int = None) -> Vector:
        """ Returns the location of the light in 3D world coordinates.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The location at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.location

    def get_rotation(self, frame: int = None) -> Euler:
        """ Returns the rotation of the light in euler angles.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The rotation at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.rotation_euler
