import random
from typing import Callable, List, Optional

import bpy
import numpy as np

from blenderproc.python.types.MeshObjectUtility import MeshObject, get_all_mesh_objects
from blenderproc.python.utility.CollisionUtility import CollisionUtility


def replace_objects(objects_to_be_replaced: List[MeshObject], objects_to_replace_with: List[MeshObject],
                    ignore_collision_with: Optional[List[MeshObject]] = None, replace_ratio: float = 1,
                    copy_properties: bool = True, max_tries: int = 100,
                    relative_pose_sampler: Callable[[MeshObject], None] = None):
    """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the objects to replace with in following steps:
    1. Randomly select a subset of objects_to_be_replaced.
    2. For each of these objects, sample other objects from objects_to_replace_with and try to replace them.
    3. In each try, the poses of the objects are aligned and a check for collisions with other objects is done.
    4. An object is skipped if max_tries is reached.

    :param objects_to_be_replaced: Objects, which should be removed from the scene.
    :param objects_to_replace_with: Objects, which will be tried to be added to the scene.
    :param ignore_collision_with: Objects, which are not checked for collisions with.
    :param replace_ratio: Ratio of objects in the original scene, which will be replaced.
    :param copy_properties: Copies the custom properties of the objects_to_be_replaced to the objects_to_replace_with.
    :param max_tries: Maximum number of tries to replace one object.
    :param relative_pose_sampler: A function that randomly perturbs the pose of the object to replace with (after it has been aligned to the object to replace).
    """
    if ignore_collision_with is None:
        ignore_collision_with = []

    # Hide new objects from renderers until they are added
    for obj in objects_to_replace_with:
        obj.hide()

    check_collision_with = []
    for obj in get_all_mesh_objects():
        if obj not in ignore_collision_with:
            check_collision_with.append(obj)

    # amount of replacements depends on the amount of objects and the replace ratio
    objects_to_be_replaced = random.sample(objects_to_be_replaced, k=int(len(objects_to_be_replaced) * replace_ratio))
    if len(objects_to_be_replaced) == 0:
        print("Warning: The amount of objects, which should be replace is zero!")

    # Go over all objects we should replace
    for current_object_to_be_replaced in objects_to_be_replaced:
        print(current_object_to_be_replaced.get_name())
        # Do at most max_tries to replace the object with a random object from  objects_to_replace_with
        tries = 0
        while tries < max_tries:
            current_object_to_replace_with = np.random.choice(objects_to_replace_with)
            if ObjectReplacer.replace(current_object_to_be_replaced, current_object_to_replace_with,
                                      check_collision_with, relative_pose_sampler=relative_pose_sampler):

                # Duplicate the added object to be able to add it again
                duplicate_new_object = current_object_to_replace_with.duplicate()

                # Copy properties to the newly duplicated object
                if copy_properties:
                    for key, value in current_object_to_be_replaced.get_all_cps():
                        duplicate_new_object.set_cp(key, value)

                duplicate_new_object.hide(False)

                print('Replaced ', current_object_to_be_replaced.get_name(), ' by ', duplicate_new_object.get_name())

                # Delete the original object and remove it from the list
                check_collision_with.remove(current_object_to_be_replaced)
                current_object_to_be_replaced.delete()
                break
            tries += 1

        if tries == max_tries:
            print("Could not replace " + current_object_to_be_replaced.get_name())


class ObjectReplacer:
    """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the
        objects to replace with, can be selected over Selectors (getter.Entity).
    """

    @staticmethod
    def _bb_ratio(bb1: np.ndarray, bb2: np.ndarray) -> list:
        """ Rough estimation of the ratios between two bounding boxes sides, not axis aligned

        :param bb1: bounding box 1. Type: float multi-dimensional array of 8 * 3.
        :param bb2: bounding box 2. Type: float multi-dimensional array of 8 * 3.
        returns the ratio between each side of the bounding box. Type: a list of floats.
        """
        ratio_a = (bb1[0, 0] - bb1[4, 0]) / (bb2[0, 0] - bb2[4, 0])
        ratio_b = (bb1[0, 1] - bb1[3, 1]) / (bb2[0, 1] - bb2[3, 1])
        ratio_c = (bb1[0, 2] - bb1[1, 2]) / (bb2[0, 2] - bb2[1, 2])
        return [ratio_a, ratio_b, ratio_c]

    @staticmethod
    def replace(obj_to_remove: MeshObject, obj_to_add: MeshObject,
                check_collision_with: Optional[List[MeshObject]] = None, scale: bool = True,
                relative_pose_sampler: Callable[[MeshObject], None] = None):
        """ Scale, translate, rotate obj_to_add to match obj_to_remove and check if there is a bounding box collision
        returns a boolean.

        :param obj_to_remove: An object to remove from the scene.
        :param obj_to_add: An object to put in the scene instead of obj_to_remove.
        :param check_collision_with: A list of objects, which are not checked for collisions with.
        :param scale: Scales obj_to_add to match obj_to_remove dimensions.
        :param relative_pose_sampler: A function that randomly perturbs the pose of the object to replace with (after it has been aligned to the object to replace).
        """
        if check_collision_with is None:
            check_collision_with = []
        # New object takes location, rotation and rough scale of original object
        obj_to_add.set_location(obj_to_remove.get_location())
        obj_to_add.set_rotation_euler(obj_to_remove.get_rotation())
        if scale:
            obj_to_add.set_scale(
                ObjectReplacer._bb_ratio(obj_to_remove.get_bound_box(True), obj_to_add.get_bound_box(True)))
        if relative_pose_sampler is not None:
            relative_pose_sampler(obj_to_add)

        # Check for collision between the new object and other objects in the scene
        return CollisionUtility.check_intersections(obj_to_add, None, [obj for obj in check_collision_with if obj != obj_to_add and obj != obj_to_remove], [])
