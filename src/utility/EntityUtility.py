from typing import Union, Any
import numpy as np

import bpy

from src.utility.StructUtility import Struct
from src.utility.Utility import Utility, KeyFrame
from mathutils import Vector, Euler, Color, Matrix

from typing import List

class Entity(Struct):

    def __init__(self, object: bpy.types.Object):
        super().__init__(object)

    @staticmethod
    def create_empty(entity_name: str, empty_type: str = "plain_axes") -> "Entity":
        """ Creates an empty entity.

        :param entity_name: The name of the new entity.
        :param empty_type: Type of the newly created empty entity. Available: ["plain_axes", "arrows", "single_arrow", \
                           "circle", "cube", "sphere", "cone"]
        :return: The new Mesh entity.
        """
        if empty_type.lower() in ["plain_axes", "arrows", "single_arrow", "circle", "cube", "sphere", "cone"]:
            bpy.ops.object.empty_add(type=empty_type.upper(), align="WORLD")
        else:
            raise RuntimeError(f'Unknown basic empty type "{empty_type}"! Available types: "plain_axes".')

        new_entity = Entity(bpy.context.object)
        new_entity.set_name(entity_name)
        return new_entity

    @staticmethod
    def convert_to_entities(blender_objects: list) -> List["Entity"]:
        """ Converts the given list of blender objects to entities

        :param blender_objects: List of blender objects.
        :return: The list of entities.
        """
        return [Entity(obj) for obj in blender_objects]

    def set_location(self, location: Union[list, Vector, np.ndarray], frame: int = None):
        """ Sets the location of the entity in 3D world coordinates.

        :param location: The location to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.location = location
        Utility.insert_keyframe(self.blender_obj, "location", frame)

    def set_rotation_euler(self, rotation_euler: Union[list, Euler, np.ndarray], frame: int = None):
        """ Sets the rotation of the entity in euler angles.

        :param rotation_euler: The euler angles to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.rotation_euler = rotation_euler
        Utility.insert_keyframe(self.blender_obj, "rotation_euler", frame)

    def set_scale(self, scale: Union[list, np.ndarray, Vector], frame: int = None):
        """ Sets the scale of the entity along all three axes.

        :param scale: The scale to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.scale = scale
        Utility.insert_keyframe(self.blender_obj, "scale", frame)

    def get_location(self, frame: int = None) -> np.ndarray:
        """ Returns the location of the entity in 3D world coordinates.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The location at the specified frame.
        """
        with KeyFrame(frame):
            return np.array(self.blender_obj.location)

    def get_rotation(self, frame: int = None) -> np.ndarray:
        """ Returns the rotation of the entity in euler angles.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The rotation at the specified frame.
        """
        with KeyFrame(frame):
            return np.array(self.blender_obj.rotation_euler)

    def get_scale(self, frame: int = None) -> np.ndarray:
        """ Returns the scale of the entity along all three axes.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The scale at the specified frame.
        """
        with KeyFrame(frame):
            return np.array(self.blender_obj.scale)

    def apply_T(self, transform: Union[np.ndarray, Matrix]):
        """ Apply the given transformation to the pose of the entity.

        :param transform: A 4x4 matrix representing the transformation.
        """
        self.blender_obj.matrix_world @= Matrix(transform)

    def set_local2world_mat(self, matrix_world: Union[np.ndarray, Matrix]):
        """ Sets the pose of the object in the form of a local2world matrix.

        :param matrix_world: A 4x4 matrix.
        """
        # To make sure matrices are always interpreted row-wise, we first convert them to a mathutils matrix.
        self.blender_obj.matrix_world = Matrix(matrix_world)

    def get_local2world_mat(self) -> np.ndarray:
        """ Returns the pose of the object in the form of a local2world matrix.

        :return: The 4x4 local2world matrix.
        """
        return np.array(self.blender_obj.matrix_world)

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

    def get_parent(self) -> "Entity":
        """ Returns the parent of the entity.

        :return: The parent.
        """
        return Entity(self.blender_obj.parent)

    def delete(self):
        """ Deletes the entity """
        bpy.ops.object.delete({"selected_objects": [self.blender_obj]})

    @staticmethod
    def delete_multiple(entities: ["Entity"]):
        """ Deletes multiple entities at once

        :param entities: A list of entities that should be deleted
        """
        bpy.ops.object.delete({"selected_objects": [e.blender_obj for e in entities]})

    def is_empty(self) -> bool:
        """ Returns whether the entity is from type "EMPTY".

        :return: True, if its an empty.
        """
        return self.blender_obj.type == "EMPTY"

    def __setattr__(self, key, value):
        if key != "blender_obj":
            raise Exception("The entity class does not allow setting any attribute. Use the corresponding method or directly access the blender attribute via entity.blender_obj.attribute_name")
        else:
            object.__setattr__(self, key, value)

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.blender_obj == other.blender_obj
        return False

    def __hash__(self):
        return hash(self.blender_obj)