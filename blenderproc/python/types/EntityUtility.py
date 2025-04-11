""" The base class of all things, which can be placed in the scene, in BlenderProc. """

from typing import Union, Optional, List
import warnings

import bpy
import numpy as np
from mathutils import Vector, Euler, Matrix

from blenderproc.python.types.StructUtility import Struct
from blenderproc.python.utility.Utility import Utility, KeyFrame


class Entity(Struct):
    """
    The entity class of all objects which can be placed inside the scene. They have a 6D pose consisting of location
    and rotation.
    """

    def update_blender_ref(self, name: str):
        """ Updates the contained blender reference using the given name of the instance.

        :param name: The name of the instance which will be used to update its blender reference.
        """
        self.blender_obj = bpy.data.objects[name]

    def set_location(self, location: Union[list, Vector, np.ndarray], frame: Optional[int] = None):
        """ Sets the location of the entity in 3D world coordinates.

        :param location: The location to set.
        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        """
        self.blender_obj.location = location
        Utility.insert_keyframe(self.blender_obj, "location", frame)

    def set_rotation_euler(self, rotation_euler: Union[list, Euler, np.ndarray], frame: Optional[int] = None):
        """ Sets the rotation of the entity in euler angles.

        :param rotation_euler: The euler angles to set.
        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        """
        self.blender_obj.rotation_euler = rotation_euler
        Utility.insert_keyframe(self.blender_obj, "rotation_euler", frame)

    def set_rotation_mat(self, rotation_mat: Union[Matrix, np.ndarray], frame: Optional[int] = None):
        """ Sets the rotation of the entity using a rotation matrix.

        :param rotation_mat: The 3x3 local to world rotation matrix.
        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        """
        self.set_rotation_euler(Matrix(rotation_mat).to_euler(), frame)

    def set_scale(self, scale: Union[list, np.ndarray, Vector], frame: Optional[int] = None):
        """ Sets the scale of the entity along all three axes.

        :param scale: The scale to set.
        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        """
        self.blender_obj.scale = scale
        Utility.insert_keyframe(self.blender_obj, "scale", frame)

    def get_location(self, frame: Optional[int] = None) -> np.ndarray:
        """ Returns the location of the entity in 3D world coordinates.

        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        :return: The location at the specified frame.
        """
        with KeyFrame(frame):
            return np.array(self.blender_obj.location)

    def get_rotation(self, frame: Optional[int] = None) -> np.ndarray:
        """ Returns the rotation of the entity in euler angles.

        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        :return: The rotation at the specified frame.
        """
        warnings.warn("This function will be deprecated. Use get_rotation_euler() instead.")
        return self.get_rotation_euler(frame)

    def get_rotation_euler(self, frame: Optional[int] = None) -> np.ndarray:
        """ Returns the rotation of the entity in euler angles.

        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        :return: The rotation at the specified frame.
        """
        with KeyFrame(frame):
            return np.array(self.blender_obj.rotation_euler)

    def get_rotation_mat(self, frame: Optional[int] = None) -> np.ndarray:
        """ Gets the rotation matrix of the entity.

        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        :return: The 3x3 local2world rotation matrix.
        """
        return np.array(Euler(self.get_rotation_euler(frame)).to_matrix())

    def get_scale(self, frame: Optional[int] = None) -> np.ndarray:
        """ Returns the scale of the entity along all three axes.

        :param frame: The frame number which the value should be set to. If None is given, the current
                      frame number is used.
        :return: The scale at the specified frame.
        """
        with KeyFrame(frame):
            return np.array(self.blender_obj.scale)

    def apply_T(self, transform: Union[np.ndarray, Matrix]):
        """ Apply the given transformation to the pose of the entity.

        :param transform: A 4x4 matrix representing the transformation.
        """
        self.blender_obj.matrix_world = Matrix(self.get_local2world_mat()) @ Matrix(transform)

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
        obj = self.blender_obj
        # Start with local2parent matrix (if obj has no parent, that equals local2world)
        matrix_world = obj.matrix_basis

        # Go up the scene graph along all parents
        while obj.parent is not None:
            # Add transformation to parent frame
            matrix_world = obj.parent.matrix_basis @ obj.matrix_parent_inverse @ matrix_world
            obj = obj.parent

        return np.array(matrix_world)

    def select(self):
        """ Selects the entity. """
        self.blender_obj.select_set(True)

    def deselect(self):
        """ Deselects the entity. """
        self.blender_obj.select_set(False)

    def duplicate(self, duplicate_children: bool = True, linked: bool = False) -> "Entity":
        """ Duplicates the object.

        :param duplicate_children: If True, also all children objects are recursively duplicated.
        :param linked: If True, object data is not copied.
        :return: A new mesh object, which is a duplicate of this object.
        """
        new_entity = self.blender_obj.copy()
        if not linked and self.blender_obj.data is not None:
            new_entity.data = self.blender_obj.data.copy()
        bpy.context.collection.objects.link(new_entity)

        duplicate_obj = convert_to_entity_subclass(new_entity)
        if type(duplicate_obj) != type(self):
            warnings.warn(f"Duplication is only partly supported for {type(self)}")

        if duplicate_children:
            for child in self.get_children():
                duplicate_child = child.duplicate(duplicate_children=duplicate_children, linked=linked)
                duplicate_child.set_parent(duplicate_obj)

                duplicate_child.blender_obj.matrix_basis = child.blender_obj.matrix_basis.copy()
                duplicate_child.blender_obj.matrix_parent_inverse = child.blender_obj.matrix_parent_inverse.copy()

        return duplicate_obj

    def clear_parent(self):
        """ Removes the object's parent and moves the object into the root level of the scene graph. """
        # Remember original object pose
        obj_pose = self.get_local2world_mat()
        self.blender_obj.parent = None
        # Make sure the object pose stays the same
        self.set_local2world_mat(obj_pose)

    def set_parent(self, new_parent: "Entity"):
        """ Sets the parent of this object.

        :param new_parent: The parent entity to set.
        """
        # If the object has already a parent object, remove it first.
        if self.blender_obj.parent is not None:
            self.clear_parent()
        self.blender_obj.parent = new_parent.blender_obj
        # Make sure the object pose stays the same => add inverse of new parent's pose to transformation chain
        self.blender_obj.matrix_parent_inverse = Matrix(new_parent.get_local2world_mat()).inverted()

    def get_parent(self) -> Optional["Entity"]:
        """ Returns the parent of the entity.

        :return: The parent.
        """
        return convert_to_entity_subclass(self.blender_obj.parent) if self.blender_obj.parent is not None else None

    def get_children(self, return_all_offspring: bool = False) -> List["Entity"]:
        """ Returns the children objects.

        :param return_all_offspring: If this is True all children and their children are recursively found and returned
        :return: A list of all children objects.
        """

        def collect_offspring(entity: bpy.types.Object) -> List[bpy.types.Object]:
            """
            Recursively collects the offspring for an entity
            """
            offspring = []
            for child in entity.children:
                offspring.append(child)
                offspring.extend(collect_offspring(child))
            return offspring

        if return_all_offspring:
            used_children = collect_offspring(self.blender_obj)
        else:
            used_children = self.blender_obj.children
        return convert_to_entities(used_children, convert_to_subclasses=True)

    def delete(self, remove_all_offspring: bool = False):
        """ Deletes the entity and maybe all of its offspring

        :param remove_all_offspring: If this is True all children and their children are recursively deleted
        """
        selected_objects = [self]
        if remove_all_offspring:
            selected_objects.extend(self.get_children(return_all_offspring=True))
        bpy.ops.object.delete({"selected_objects": [e.blender_obj for e in selected_objects]})

    def is_empty(self) -> bool:
        """ Returns whether the entity is from type "EMPTY".

        :return: True, if its an empty.
        """
        return self.blender_obj.type == "EMPTY"

    def hide(self, hide_object: bool = True):
        """ Sets the visibility of the object.

        :param hide_object: Determines whether the object should be hidden in rendering.
        """
        self.blender_obj.hide_render = hide_object

    def is_hidden(self) -> bool:
        """ Returns whether the object is hidden in rendering.

        :return: True, if it is hidden.
        """
        return self.blender_obj.hide_render

    def __setattr__(self, key, value):
        if key != "blender_obj":
            raise RuntimeError("The entity class does not allow setting any attribute. Use the corresponding "
                               "method or directly access the blender attribute via entity.blender_obj.attribute_name")
        object.__setattr__(self, key, value)

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.blender_obj == other.blender_obj
        return False

    def __hash__(self):
        return hash(self.blender_obj)


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


def convert_to_entities(blender_objects: list, convert_to_subclasses: bool = False) -> List["Entity"]:
    """ Converts the given list of blender objects to entities

    :param blender_objects: List of blender objects.
    :param convert_to_subclasses: If True, each blender object will be wrapped into an entity subclass based
                                  on the type of object.
    :return: The list of entities.
    """
    if not convert_to_subclasses:
        return [Entity(obj) for obj in blender_objects]
    return [convert_to_entity_subclass(obj) for obj in blender_objects]


def convert_to_entity_subclass(blender_object: bpy.types.Object) -> "Entity":
    """ Converts the given blender object into our respective wrapper class.

    :param blender_object: The blender object.
    :return: The wrapped object.
    """
    if blender_object.type == 'MESH':
        # pylint: disable=import-outside-toplevel,cyclic-import
        from blenderproc.python.types.MeshObjectUtility import MeshObject
        # pylint: enable=import-outside-toplevel,cyclic-import
        return MeshObject(blender_object)
    if blender_object.type == 'LIGHT':
        # pylint: disable=import-outside-toplevel,cyclic-import
        from blenderproc.python.types.LightUtility import Light
        # pylint: enable=import-outside-toplevel,cyclic-import
        return Light(blender_obj=blender_object)
    return Entity(blender_object)


def delete_multiple(entities: List[Union["Entity"]], remove_all_offspring: bool = False):
    """ Deletes multiple entities at once

    :param entities: A list of entities that should be deleted
    :param remove_all_offspring: If this is True all children and their children are recursively deleted
    """

    if remove_all_offspring:
        all_nodes = []
        for entity in entities:
            all_nodes.append(entity)
            all_nodes.extend(entity.get_children(return_all_offspring=True))
        # avoid doubles
        all_nodes = set(all_nodes)
        bpy.ops.object.delete({"selected_objects": [e.blender_obj for e in all_nodes]})
    else:
        bpy.ops.object.delete({"selected_objects": [e.blender_obj for e in entities]})
