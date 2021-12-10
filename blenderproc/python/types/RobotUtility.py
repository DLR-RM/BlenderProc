from typing import Union, List
import numpy as np
from mathutils import Matrix
import urdfpy

import bpy

from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.ArmatureUtility import Armature


class Inertial(Entity):
    def __init__(self, bpy_object: bpy.types.Object):
        super().__init__(bpy_object=bpy_object)

        object.__setattr__(self, "inertia", None)
        object.__setattr__(self, "mass", None)
        object.__setattr__(self, "origin", None)

    def set_inertia(self, inertia: np.ndarray):
        """ Sets inertia value.

        :param inertia: 3x3 symmetric rotational inertia matrix.
        """
        assert inertia.shape == (3, 3)
        object.__setattr__(self, "inertia", inertia)

    def get_inertia(self) -> np.ndarray:
        """ Returns the inertia.

        :return: The inertia matrix.
        """
        return self.inertia

    def set_mass(self, mass: float):
        """ Sets the mass.

        :param mass: Mass of the link in kilograms.
        """
        object.__setattr__(self, "mass", mass)

    def get_mass(self) -> float:
        """ Returns the mass of the link.

        :return: The mass.
        """
        return self.mass

    def set_origin(self, origin: Union[np.ndarray, Matrix]):
        """ Sets the origin and the world matrix of the inertia.

        :param origin: 4x4 matrix of the inertials relative to the link frame.
        """
        object.__setattr__(self, "origin", Matrix(origin))
        self.blender_obj.matrix_world = Matrix(origin)

    def get_origin(self) -> Matrix:
        """ Returns the origin of the inertia.

        :return: The pose relative to the link frame.
        """
        return self.origin


class Link(Armature):
    def __init__(self, bpy_object):
        super().__init__(bpy_object=bpy_object)

        object.__setattr__(self, 'visuals', [])
        object.__setattr__(self, 'inertial', None)
        object.__setattr__(self, 'collisions', [])
        object.__setattr__(self, 'joint_type', None)

    def get_children(self) -> List[Union[MeshObject, Inertial]]:
        """ Returns all children of the link. These don't necessarily have a relationship to the link (yet).

        :return: List of children.
        """
        children = self.get_collisions() + self.get_visuals()
        if self.inertial is not None:
            children.append(self.inertial)
        return children

    def set_joint_type(self, joint_type: Union[str, None]):
        """ Sets the joint type of the link which specifies the connection to its parent.

        :param joint_type: One of ['fixed', 'prismatic', 'revolute', 'continuous', 'planar', 'floating' or None].
        """
        object.__setattr__(self, "joint_type", joint_type)

    def get_joint_type(self) -> Union[str, None]:
        """ Returns the joint type.

        :return: The joint type of the armature.
        """
        return self.joint_type

    def set_visuals(self, visuals: List[MeshObject]):
        """ Sets the visual objects of the link.

        :param visuals: List of visual objects.
        """
        if not isinstance(visuals, list):
            visuals = [visuals]
        self.visuals.extend([visual for visual in visuals if visual not in self.visuals])

    def get_visuals(self) -> List[MeshObject]:
        """ Returns the list of visual objects of the link.

        :return: List of visual objects.
        """
        return self.visuals

    def set_inertial(self, inertial: Inertial):
        """ Sets the inertial object of the link.

        :param inertial: Inertial object.
        """
        object.__setattr__(self, "inertial", inertial)

    def get_inertial(self) -> Inertial:
        """ Returns the inertial object of the link.

        :return: Inertial object of the link.
        """
        return self.inertial

    def set_collisions(self, collisions: List[MeshObject]):
        """ Sets the collision objects of the link.

        :param collisions: List of collision objects.
        """
        if not isinstance(collisions, list):
            collisions = [collisions]
        self.collisions.extend([collision for collision in collisions if collision not in self.collisions])

    def get_collisions(self) -> List[MeshObject]:
        """ Returns the list of collision objects of the link.

        :return: List of collision objects.
        """
        return self.collisions


class Robot(Entity):
    def __init__(self, name: str, links: List[Link], other_xml: Union[urdfpy.URDF, None] = None):
        super().__init__(bpy_object=links[0].blender_obj)  # allows full manipulation (translation, scale, rotation) of whole robot
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "links", links)
        object.__setattr__(self, "other_xml", other_xml)

    def get_all_robot_objs(self) -> List[Union[Link, Inertial, MeshObject]]:
        """ Returns a list of all robot-related objects.

        :return: List of all robot-related objects.
        """
        objs = []
        for link in self.links:
            objs.append(link)
            objs.extend(link.get_children())
        return objs

    def get_all_collision_objs(self) -> List[MeshObject]:
        """ Returns a list of all collision objects.

        :return: List of all collision objects.
        """
        return [obj for obj in self.get_all_robot_objs() if 'collision' in obj.get_name()]

    def get_all_inertial_objs(self) -> List[Inertial]:
        """ Returns a list of all inertial objects.

        :return: List of all inertial objects.
        """
        return [obj for obj in self.get_all_robot_objs() if isinstance(obj, Inertial)]

    def get_all_visual_objs(self) -> List[MeshObject]:
        """ Returns a list of all visual objects.

        :return: List of all visual objects.
        """
        return [obj for obj in self.get_all_robot_objs() if 'visual' in obj.get_name()]

    def hide_irrelevant_objs(self):
        """ Hides links and their respective collision and inertial objects from rendering. """
        for link in self.links:
            link.hide()
            for child in link.blender_obj.children:
                if isinstance(child, bpy.types.Object):
                    child = MeshObject(child)
                if 'collision' in child.get_name() or 'inertial' in child.get_name():
                    child.hide()

    def set_ascending_category_ids(self, category_ids: Union[List[int], None] = None):
        """ Sets semantic categories to the links and their associated objects.

        :param category_ids: List of 'category_id's for every link. If None, will create a list from [1 ... len(links)].
        """
        if category_ids is None:
            category_ids = list(range(1, len(self.links) + 1))

        assert len(category_ids) == len(self.links), f"Need equal amount of category ids for links. Got {len(category_ids)} and {len(self.links)}, respectively."
        for link, category_id in zip(self.links, category_ids):
            link.set_cp(key="category_id", value=category_id)
            for obj in link.get_children():
                obj.set_cp(key="category_id", value=category_id)

    def remove_link_by_index(self, index: int = 0):
        """ Removes a link and all its associated objects given an index. Also handles relationship of the link's child with its parent.
        This is useful for removing a 'world link' which could be a simple flat surface, or if someone wants to shorten the robot.

        :param index: Index of the joint to be removed.
        """
        assert index < len(self.links), f"Invalid index {index}. Index must be in range 0, {len(self.links)} (no. links: {len(self.links)})."

        # remove link from robot instance and determine child / parent
        parent = self.links[index - 1] if index != 0 else None
        child = self.links[index + 1] if index != len(self.links) else None
        link_to_be_removed = self.links.pop(index)

        # calculate new transformation of child and set new parent
        if child is not None:
            child.blender_obj.matrix_world = link_to_be_removed.blender_obj.matrix_world
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, properties=True)

            # handle new parent-child relationship
            if parent is not None:
                bpy.ops.object.select_all(action='DESELECT')
                parent.select()
                child.select()

                # select which object to parent to
                bpy.context.view_layer.objects.active = parent.blender_obj

                # parent object
                bpy.ops.object.posemode_toggle()
                bpy.ops.object.parent_set(type="BONE")
                bpy.ops.object.posemode_toggle()

        # set new base in case the original base will be removed
        if index == 0:
            super().__init__(bpy_object=self.links[0].blender_obj)

        # finally, delete the link and all its children
        for obj in link_to_be_removed.get_children():
            obj.delete()
        link_to_be_removed.delete()

    def set_name(self, name: str):
        """ Sets the name of the robot.

        :param name: The new name.
        """
        self.name = name

    def get_name(self) -> str:
        """ Returns the name of the robot.

        :return: The name.
        """
        return self.name

    def hide(self, hide_object: bool = True):
        """ Sets the visibility of the object.

        :param hide_object: Determines whether the object should be hidden in rendering.
        """
        for link in self.links:
            link.hide(hide_object=hide_object)
            for child in link.get_children():
                child.hide(hide_object=hide_object)

    def get_all_local2world_mats(self):
        """ Returns all matrix_world matrices from every joint. """

        return np.stack([link.blender_obj.matrix_world for link in self.links])
