
from src.main.Module import Module
import bpy
import random
import numpy as np
import math
from src.utility.BlenderUtility import check_intersection, check_bb_intersection, duplicate_objects, get_all_mesh_objects

class ObjectReplacer(Module):
    """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the objects to replace with, can be selected over Selectors (getter.Entity).
    **Configuration**:
    .. csv-table::
       :header: "Parameter", "Description"

       "replace_ratio", "Ratio of objects in the original scene, which are tried to be replaced. Type: float. Default value: 1."
       "copy_properties", "Copies the custom properties of the objects_to_be_replaced to the objects_to_replace_with. Type: boolean. Default value: True."
       "objects_to_be_replaced", "Provider (Getter) in order to select objects to try to remove from the scene, gets list of object on a certain condition. Type: Getter. Default value: []."
       "objects_to_replace_with", "Provider (Getter) in order to select objects to try to add to the scene, gets list of object on a certain condition. Type Getter. Default value: []"
       "ignore_collision_with", "Provider (Getter) in order to select objects to not check for collisions with. Type：Getter. Default value: []."
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self._replace_ratio = self.config.get_float("replace_ratio", 1)
        self._copy_properties = self.config.get_float("copy_properties", 1)

    def _replace_and_edit(self, obj_to_remove, obj_to_add, scale=True):
        """
        Scale, translate, rotate obj_to_add to match obj_to_remove and check if there is a bounding box collision
        returns a boolean.

        :param obj_to_remove: object to remove from the scene
        :param obj_to_add: object to put in the scene instead of obj_to_remove
        :param scale: Scales obj_to_add to match obj_to_remove dimensions
        """        
        
        def _bb_ratio(bb1, bb2):
            """
            Rough estimation of the ratios between two bounding boxes sides, not axis aligned

            :param bb1: bounding box 1
            :param bb2: bounding box 2
            returns a list of floats.
            """

            def _two_points_distance(point1, point2):
                """
                Eclidian distance between two points

                :param point1: Point 1 as a list of three floats
                :param point2: Point 2 as a list of three floats
                returns a float.
                """
                return np.linalg.norm(np.array(point1) - np.array(point2))
            
            ratio_a = _two_points_distance(bb1[0], bb1[3]) / _two_points_distance(bb2[0], bb2[3])
            ratio_b = _two_points_distance(bb1[0], bb1[4]) / _two_points_distance(bb2[0], bb2[4])
            ratio_c = _two_points_distance(bb1[0], bb1[1]) / _two_points_distance(bb2[0], bb2[1])
            return [ratio_a, ratio_b, ratio_c]
        
        # New object takes location, rotation and rough scale of original object
        bpy.ops.object.select_all(action='DESELECT')
        obj_to_add.select_set(True)
        obj_to_add.location = obj_to_remove.location
        obj_to_add.rotation_euler = obj_to_remove.rotation_euler
        if scale:
            obj_to_add.scale = _bb_ratio(obj_to_remove.bound_box, obj_to_add.bound_box)

        # Check for collision between the new object and other objects in the scene
        can_replace = True
        for obj in get_all_mesh_objects(): # for each object

            if obj != obj_to_add and obj_to_remove != obj and obj not in self._ignore_collision_with:
                if check_bb_intersection(obj, obj_to_add):
                    if check_intersection(obj, obj_to_add)[0]:
                        can_replace = False
                        break
        return can_replace

    def run(self):
        self._objects_to_be_replaced = self.config.get_list("objects_to_be_replaced", [])
        self._objects_to_replace_with = self.config.get_list("objects_to_replace_with", [])
        self._ignore_collision_with = self.config.get_list("ignore_collision_with", [])

        # Now we have two lists to do the replacing
        # Replace a ratio of the objects in the scene with the list of the provided objects randomly
        indices = np.random.choice(len(self._objects_to_replace_with), int(self._replace_ratio * len(self._objects_to_be_replaced)))
        for idx, new_obj_idx in enumerate(indices):

            # More than one original object could be replaced by just one object
            original_object = self._objects_to_be_replaced[idx]
            new_object = self._objects_to_replace_with[new_obj_idx]

            if self._replace_and_edit(original_object, new_object):

                # Copy properties
                if self._copy_properties:
                    for key, value in original_object.items():
                        new_object[key] = value

                # Duplicate the added object to be able to add it again.
                duplicates = duplicate_objects(new_object) 
                if len(duplicates) == 1:
                    self._objects_to_replace_with[new_obj_idx] = duplicates[0]
                else:
                    raise Exception("No object to duplicate")

                # Update the scene
                new_object.hide_render = False
                print('Replaced ', original_object.name, ' by ', new_object.name)

                # Delete the original object
                bpy.ops.object.select_all(action='DESELECT')
                original_object.select_set(True)
                bpy.ops.object.delete()
            else:
                print('Collision happened while replacing an object, falling back to original one.')

        bpy.context.view_layer.update()
