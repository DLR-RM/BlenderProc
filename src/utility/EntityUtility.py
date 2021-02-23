from typing import Union, Any

import bpy
from src.utility.Utility import Utility, KeyFrame
from mathutils import Vector, Euler, Color, Matrix

from typing import List

class Entity:

    def __init__(self, object: bpy.types.Object):
        self.blender_obj = object

    @staticmethod
    def convert_to_entities(blender_objects: list) -> List["Entity"]:
        """ Converts the given list of blender objects to entities

        :param blender_objects: List of blender objects.
        :return: The list of entities.
        """
        return [Entity(obj) for obj in blender_objects]

    def set_name(self, name: str):
        """ Sets the name of the entity.

        :param name: The new name.
        """
        self.blender_obj.name = name

    def get_name(self) -> str:
        """ Returns the name of the entity.

        :return: The name.
        """
        return self.blender_obj.name

    def set_location(self, location: Union[list, Vector], frame: int = None):
        """ Sets the location of the entity in 3D world coordinates.

        :param location: The location to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.location = location
        Utility.insert_keyframe(self.blender_obj, "location", frame)

    def set_rotation_euler(self, rotation_euler: Union[list, Euler], frame: int = None):
        """ Sets the rotation of the entity in euler angles.

        :param rotation_euler: The euler angles to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.rotation_euler = rotation_euler
        Utility.insert_keyframe(self.blender_obj, "rotation_euler", frame)

    def set_scale(self, scale: Union[list, Vector], frame: int = None):
        """ Sets the scale of the entity along all three axes.

        :param scale: The scale to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.scale = scale
        Utility.insert_keyframe(self.blender_obj, "scale", frame)

    def get_location(self, frame: int = None) -> Vector:
        """ Returns the location of the entity in 3D world coordinates.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The location at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.location

    def get_rotation(self, frame: int = None) -> Euler:
        """ Returns the rotation of the entity in euler angles.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The rotation at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.rotation_euler

    def get_scale(self, frame: int = None) -> Vector:
        """ Returns the scale of the entity along all three axes.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The scale at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.scale

    def apply_T(self, transform: Matrix):
        """ Apply the given transformation to the pose of the entity.

        :param transform: A 4x4 matrix representing the transformation.
        """
        self.blender_obj.matrix_world @= transform

    def set_local2world_mat(self, matrix_world: Matrix):
        """ Sets the pose of the object in the form of a local2world matrix.

        :param matrix_world: A 4x4 matrix.
        """
        self.blender_obj.matrix_world = matrix_world

    def get_local2world_mat(self) -> Matrix:
        """ Returns the pose of the object in the form of a local2world matrix.

        :return: The 4x4 local2world matrix.
        """
        return self.blender_obj.matrix_world

    def get_cp(self, key: str, frame: int = None) -> Any:
        """ Returns the custom property with the given key.

        :param key: The key of the custom property.
        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The value of the custom property.
        """
        with KeyFrame(frame):
            return self.blender_obj[key]

    def set_cp(self, key: str, value: Any, frame: int = None):
        """ Sets the custom property with the given key.

        Keyframes can be only set for custom properties from type int, float or bool.

        :param key: The key of the custom property.
        :param value: The value to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj[key] = value
        if isinstance(self.blender_obj[key], float) or isinstance(self.blender_obj[key], int):
            Utility.insert_keyframe(self.blender_obj, "[\"" + key + "\"]", frame)

    def del_cp(self, key):
        """ Removes the custom property with the given key.

        :param key: The key of the custom property to remove.
        """
        del self.blender_obj[key]

    def has_cp(self, key: str) -> bool:
        """ Return whether a custom property with the given key exists.

        :param key: The key of the custom property to check.
        :return: True, if the custom property exists.
        """
        return key in self.blender_obj

    def clear_all_cps(self):
        """ Removes all existing custom properties the entity has. """
        keys = self.blender_obj.keys()
        for key in keys:
            del self.blender_obj[key]

    def select(self):
        """ Selects the entity. """
        self.blender_obj.select_set(True)

    def deselect(self):
        """ Deselects the entity. """
        self.blender_obj.select_set(False)

    def set_parent(self, parent: "Entity"):
        """ Sets the parent of entity.

        :param parent: The parent entity to set.
        """
        self.blender_obj.parent = parent.blender_obj

    def __setattr__(self, key, value):
        if key != "blender_obj":
            raise Exception("The entity class does not allow setting any attribute. Use the corresponding method or directly access the blender attribute via entity.blender_obj.attribute_name")
        else:
            object.__setattr__(self, key, value)