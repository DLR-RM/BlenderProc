
from src.main.Module import Module
import bpy
import random
import numpy as np
import math
from collections import defaultdict
from src.utility.BlenderUtility import check_intersection, duplicate_objects, check_bb_intersection
from src.utility.Utility import Utility
from src.utility.Config import Config

class ObjectReplacer(Module):
    """ Replaces each object against another object and scales it according to the bounding box, the replaced objects and the objects to replace with, can be selected over Selectors (getter.Entity).
    **Configuration**:
    .. csv-table::
       :header: "Parameter", "Description"

       "replace_ratio", "Ratio of objects in the orginal scene to try replacing."
       "objects_to_be_replaced", "Provider (Getter) in order to select objects to try to remove from the scene, gets list of object on a certain condition"
       "objects_to_replace_with", "Provider (Getter) in order to select objects to try to add to the scene, gets list of object on a certain condition"
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self._replace_ratio = self.config.get_float("replace_ratio", 1)

    def _two_points_distance(self, point1, point2):
        """
        Eclidian distance between two points

        :param point1: Point 1
        :param point2: Point 2
        returns a float.
        """
        return np.linalg.norm(np.array(point1) - np.array(point2))
        
    def _bb_volume_ratio(self, bb1, bb2):
        """
        Ratios between two bounding boxes volumes

        :param bb1: bounding box 1
        :param bb2: bounding box 2
        returns a list of floats.
        """
        # Multiply the three sides of the bb
        v1 = self._two_points_distance(bb1[0], bb1[3]) * self._two_points_distance(bb1[0], bb1[4]) * self._two_points_distance(bb1[0], bb1[1])
        v2 = self._two_points_distance(bb2[0], bb2[3]) * self._two_points_distance(bb2[0], bb2[4]) * self._two_points_distance(bb2[0], bb2[1])
        return v1/v2

    def _can_replace(self, obj1, obj2, scale=True):
        """
        Scale, translate, rotate obj2 to match obj1 and check if there is a bounding box collision

        :param obj1: object to remove from the scene
        :param obj2: object to put in the scene instead of obj1
        :param scale: Scales obj2 to match obj1 dimensions
        returns a boolean.
        """        
        bpy.ops.object.select_all(action='DESELECT')
        obj2.select_set(True)
        obj2.location = obj1.location
        obj2.rotation_euler = obj1.rotation_euler
        if scale:
            obj2.scale = [self._bb_volume_ratio(obj1.bound_box, obj2.bound_box)] * 3

        # Check for collision between the new object and other objects in the scene
        intersection = False
        for obj in BlenderUtility.get_all_mesh_objects():
            if obj != obj2 and obj1 != obj:
                intersection = check_bb_intersection(obj, obj2)
                if intersection:
                    intersection = check_intersection(obj, obj2)[0]
                    if intersection:
                        break
        return not intersection

    def run(self):
        self._objects_to_be_replaced = self.config.get_list("objects_to_be_replaced")
        self._objects_to_replace_with = self.config.get_list("objects_to_replace_with")

        # Now we have two lists to do the replacing
        # Replace a ratio of the objects in the scene with the list of the provided ikea objects randomly
        indices = np.random.choice(len(self._objects_to_replace_with), int(self._replace_ratio * len(self._objects_to_be_replaced)))
        for idx, new_obj_idx in enumerate(indices):
            # More than one original object could be replaced by just one object
            original_object = self._objects_to_be_replaced[idx]
            new_object = self._objects_to_replace_with[new_obj_idx]

            if self._can_replace(original_object, new_object):
                # Duplicate the added object to be able to add it again.
                new_object['category_id'] = original_object['category_id']
                if len(duplicate_objects(new_object)) > 0:
                    self._objects_to_replace_with[new_obj_idx] = duplicate_objects(new_object)[0]

                # Update the scene
                original_object.hide_render = True
                new_object.hide_render = False
                
                print('Replaced', original_object.name, ' by a ', new_object.name)

                # Delete the original object
                bpy.ops.object.select_all(action='DESELECT')
                original_object.select_set(True)
                bpy.ops.object.delete()
            else:
                print('Collision happened while replacing an object, falling back to original one.')

        bpy.context.view_layer.update()
