import bpy
import numpy as np

from src.utility.BlenderUtility import check_intersection, check_bb_intersection, get_all_blender_mesh_objects
from src.utility.MeshObjectUtility import MeshObject
from src.utility.ProviderUtility import get_all_mesh_objects


class ObjectReplacer:
    """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the
        objects to replace with, can be selected over Selectors (getter.Entity).
    """

    @staticmethod
    def _bb_ratio(bb1, bb2):
        """ Rough estimation of the ratios between two bounding boxes sides, not axis aligned

        :param bb1: bounding box 1. Type: float multi-dimensional array of 8 * 3.
        :param bb2: bounding box 2. Type: float multi-dimensional array of 8 * 3.
        returns the ratio between each side of the bounding box. Type: a list of floats.
        """
        ratio_a = (bb1[0][0] - bb1[4][0]) / (bb2[0][0] - bb2[4][0])
        ratio_b = (bb1[0][1] - bb1[3][1]) / (bb2[0][1] - bb2[3][1])
        ratio_c = (bb1[0][2] - bb1[1][2]) / (bb2[0][2] - bb2[1][2])
        return [ratio_a, ratio_b, ratio_c]

    @staticmethod
    def replace(obj_to_remove: MeshObject, obj_to_add: MeshObject, check_collision_with: [MeshObject] = [], scale: bool = True):
        """ Scale, translate, rotate obj_to_add to match obj_to_remove and check if there is a bounding box collision
        returns a boolean.

        :param obj_to_remove: An object to remove from the scene.
        :param obj_to_add: An object to put in the scene instead of obj_to_remove.
        :param check_collision_with: A list of objects, which are not checked for collisions with.
        :param scale: Scales obj_to_add to match obj_to_remove dimensions.
        """
        # New object takes location, rotation and rough scale of original object
        obj_to_add.set_location(obj_to_remove.get_location())
        obj_to_add.set_rotation_euler(obj_to_remove.get_rotation())
        if scale:
            obj_to_add.set_scale(ObjectReplacer._bb_ratio(obj_to_remove.get_bound_box(True), obj_to_add.get_bound_box(True)))
        bpy.context.view_layer.update()

        # Check for collision between the new object and other objects in the scene
        for obj in check_collision_with: # for each object
            if obj != obj_to_add and obj_to_remove != obj:
                if check_bb_intersection(obj.blender_obj, obj_to_add.blender_obj):
                    if check_intersection(obj.blender_obj, obj_to_add.blender_obj)[0]:
                        return False
        return True

    @staticmethod
    def replace_multiple(objects_to_be_replaced: [MeshObject], objects_to_replace_with: [MeshObject], ignore_collision_with: [MeshObject] = [], replace_ratio: float = 1, copy_properties: bool = True, max_tries: int = 100000):
        """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the objects to replace with in following steps:
        1. Find which object to replace.
        2. Place the new object in place of the object to be replaced and scale accordingly.
        2. If there is no collision, between that object and the objects in the scene, then do replace and delete the original object.

        :param objects_to_be_replaced: Objects, which should be removed from the scene.
        :param objects_to_replace_with: Objects, which will be tried to be added to the scene.
        :param ignore_collision_with: Objects, which are not checked for collisions with.
        :param replace_ratio: Ratio of objects in the original scene, which will be replaced.
        :param copy_properties: Copies the custom properties of the objects_to_be_replaced to the objects_to_replace_with.
        :param max_tries: Amount of tries, which are performed while trying to replace the objects.
        """
        # Hide new objects from renderers until they are added
        for obj in objects_to_replace_with:
            obj.hide()

        check_collision_with = []
        for obj in get_all_mesh_objects():
            if obj not in ignore_collision_with:
                check_collision_with.append(obj)

        # amount of replacements depends on the amount of objects and the replace ratio
        amount_of_replacements = int(len(objects_to_be_replaced) * replace_ratio)
        if amount_of_replacements == 0:
            print("Warning: The amount of objects, which should be replace is zero!")
        amount_of_already_replaced = 0
        tries = 0

        # tries to replace objects until the amount of requested objects are replaced or the amount
        # of maximum tries was reached
        while amount_of_already_replaced < amount_of_replacements and tries < max_tries:
            current_object_to_be_replaced = np.random.choice(objects_to_be_replaced)
            current_object_to_replace_with = np.random.choice(objects_to_replace_with)
            if ObjectReplacer.replace(current_object_to_be_replaced, current_object_to_replace_with, check_collision_with):

                # Duplicate the added object to be able to add it again
                duplicate_new_object = current_object_to_replace_with.duplicate()

                # Copy properties to the newly duplicated object
                if copy_properties:
                    for key, value in current_object_to_be_replaced.get_all_cps():
                        duplicate_new_object.set_cp(key, value)

                duplicate_new_object.hide(False)

                print('Replaced ', current_object_to_be_replaced.get_name(), ' by ', duplicate_new_object.get_name())

                # Delete the original object and remove it from the list
                objects_to_be_replaced.remove(current_object_to_be_replaced)
                check_collision_with.remove(current_object_to_be_replaced)
                current_object_to_be_replaced.delete()

                amount_of_already_replaced += 1

            if not objects_to_be_replaced:
                # if no objects are left to replace, break the loop
                break
            tries += 1
        bpy.context.view_layer.update()
