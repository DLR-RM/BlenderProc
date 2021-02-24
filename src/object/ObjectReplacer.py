import bpy
import numpy as np

from src.main.Module import Module
from src.utility.BlenderUtility import check_intersection, check_bb_intersection, duplicate_objects, get_all_blender_mesh_objects


class ObjectReplacer(Module):
    """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the
        objects to replace with, can be selected over Selectors (getter.Entity).

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - replace_ratio
          - Ratio of objects in the original scene, which will be replaced. Default: 1.
          - float
        * - copy_properties
          - Copies the custom properties of the objects_to_be_replaced to the objects_to_replace_with. Default:
            True.
          - bool
        * - objects_to_be_replaced
          - Provider (Getter): selects objects, which should be removed from the scene, gets list of objects
            following a certain condition. Default: [].
          - Provider
        * - objects_to_replace_with
          - Provider (Getter): selects objects, which will be tried to be added to the scene, gets list of objects
            following a certain condition. Default: [].
          - Provider
        * - ignore_collision_with
          - Provider (Getter): selects objects, which are not checked for collisions with. Default: [].
          - Provider
        * - max_tries
          - Amount of tries, which are performed while trying to replace the objects. Default: 100000.
          - int
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self._replace_ratio = self.config.get_float("replace_ratio", 1)
        self._copy_properties = self.config.get_float("copy_properties", 1)
        self._max_tries = self.config.get_int("max_tries", 100000)
        self._objects_to_be_replaced = []
        self._objects_to_replace_with = []
        self._ignore_collision_with = []

    def _replace_and_edit(self, obj_to_remove, obj_to_add, scale=True):
        """
        Scale, translate, rotate obj_to_add to match obj_to_remove and check if there is a bounding box collision
        returns a boolean.

        :param obj_to_remove: object to remove from the scene. Type: blender object.
        :param obj_to_add: object to put in the scene instead of obj_to_remove. Type: blender object.
        :param scale: Scales obj_to_add to match obj_to_remove dimensions. Type: bool.
        """        
        
        def _bb_ratio(bb1, bb2):
            """
            Rough estimation of the ratios between two bounding boxes sides, not axis aligned

            :param bb1: bounding box 1. Type: float multi-dimensional array of 8 * 3.
            :param bb2: bounding box 2. Type: float multi-dimensional array of 8 * 3.
            returns the ratio between each side of the bounding box. Type: a list of floats.
            """

            def _two_points_distance(point1, point2):
                """
                Eclidian distance between two points

                :param point1: Point 1 as a list of three floats. Type: list.
                :param point2: Point 2 as a list of three floats. Type: list.
                returns a float.
                """
                return np.linalg.norm(np.array(point1) - np.array(point2))
            
            ratio_a = _two_points_distance(bb1[0], bb1[3]) / _two_points_distance(bb2[0], bb2[3])
            ratio_b = _two_points_distance(bb1[0], bb1[4]) / _two_points_distance(bb2[0], bb2[4])
            ratio_c = _two_points_distance(bb1[0], bb1[1]) / _two_points_distance(bb2[0], bb2[1])
            return [ratio_a, ratio_b, ratio_c]
        
        # New object takes location, rotation and rough scale of original object
        obj_to_add.location = obj_to_remove.location
        obj_to_add.rotation_euler = obj_to_remove.rotation_euler
        if scale:
            obj_to_add.scale = _bb_ratio(obj_to_remove.bound_box, obj_to_add.bound_box)

        # Check for collision between the new object and other objects in the scene
        for obj in get_all_blender_mesh_objects(): # for each object

            if obj != obj_to_add and obj_to_remove != obj and obj not in self._ignore_collision_with:
                if check_bb_intersection(obj, obj_to_add):
                    if check_intersection(obj, obj_to_add)[0]:
                        return False
        return True

    def run(self):
        """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the objects to replace with in following steps:
        1. Find which object to replace.
        2. Place the new object in place of the object to be replaced and scale accordingly.
        2. If there is no collision, between that object and the objects in the scene, then do replace and delete the original object.

        """
        self._objects_to_be_replaced = self.config.get_list("objects_to_be_replaced", [])
        self._objects_to_replace_with = self.config.get_list("objects_to_replace_with", [])
        self._ignore_collision_with = self.config.get_list("ignore_collision_with", [])

        # Hide new objects from renderers until they are added
        for obj in self._objects_to_replace_with:
            obj.hide_render = True

        # amount of replacements depends on the amount of objects and the replace ratio
        amount_of_replacements = int(len(self._objects_to_be_replaced) * self._replace_ratio)
        if amount_of_replacements == 0:
            print("Warning: The amount of objects, which should be replace is zero!")
        amount_of_already_replaced = 0
        tries = 0

        # tries to replace objects until the amount of requested objects are replaced or the amount
        # of maximum tries was reached
        while amount_of_already_replaced < amount_of_replacements and tries < self._max_tries:
            current_object_to_be_replaced = np.random.choice(self._objects_to_be_replaced)
            current_object_to_replace_with = np.random.choice(self._objects_to_replace_with)
            if self._replace_and_edit(current_object_to_be_replaced, current_object_to_replace_with):

                # Duplicate the added object to be able to add it again
                duplicates = duplicate_objects(current_object_to_replace_with)
                if len(duplicates) == 1:
                    duplicate_new_object = duplicates[0]
                else:
                    raise Exception("The duplication failed, amount of objects are: {}".format(len(duplicates)))

                # Copy properties to the newly duplicated object
                if self._copy_properties:
                    for key, value in current_object_to_be_replaced.items():
                        duplicate_new_object[key] = value

                duplicate_new_object.hide_render = False

                print('Replaced ', current_object_to_replace_with.name, ' by ', duplicate_new_object.name)

                # Delete the original object and remove it from the list
                self._objects_to_replace_with.remove(current_object_to_replace_with)
                bpy.ops.object.select_all(action='DESELECT')
                current_object_to_replace_with.select_set(True)
                bpy.ops.object.delete()

                amount_of_already_replaced += 1

            tries += 1
        bpy.context.view_layer.update()
