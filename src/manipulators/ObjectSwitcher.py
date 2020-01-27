
from src.main.Module import Module
import bpy
import random
import numpy as np
import math
from collections import defaultdict
from src.utility.BlenderUtility import check_bb_intersection
from src.utility.Utility import Utility
from src.utility.Config import Config

class ObjectSwitcher(Module):
    """ Randomly switch between objects in the scene and other objects loaded using Loader.IkeaObjectsLoader.
    **Configuration**:
    .. csv-table::
       :header: "Parameter", "Description"
       "switch_ratio", "Ratio of objects in the orginal scene to try replacing."
       "ikea_objects_loader", "loader.IkeaObjectsLoader"
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self._switch_ratio = self.config.get_float("switch_ratio", 1)
        self._ikea_objects_selector = config.get_raw_dict("selector", {})

    def _two_points_distance(self, point1, point2):
        """
        :param point1: Point 1
        :param point2: Point 2
        Eclidian distance between two points
        returns a float.
        """
        locx = point2[0] - point1[0]
        locy = point2[1] - point1[1]
        locz = point2[2] - point1[2]
        distance = math.sqrt((locx)**2 + (locy)**2 + (locz)**2) 
        return distance

    def _bb_ratio(self, bb1, bb2):
        """
        :param bb1: bounding box 1
        :param bb2: bounding box 2
        Ratios between two bounding boxes 3 sides
        returns a list of floats.
        """
        ratio_a = self._two_points_distance(bb1[0], bb1[3]) / self._two_points_distance(bb2[0], bb2[3])
        ratio_b = self._two_points_distance(bb1[0], bb1[4]) / self._two_points_distance(bb2[0], bb2[4])
        ratio_c = self._two_points_distance(bb1[0], bb1[1]) / self._two_points_distance(bb2[0], bb2[1])
        return [ratio_a, ratio_b, ratio_c]

    def _can_replace(self, obj1, obj2, scale=True):
        """
        :param obj1: object to remove from the scene
        :param obj2: object to put in the scene instead of obj1
        :param scale: Scales obj2 to match obj1 dimensions
        Scale, translate, rotate obj2 to match obj1 and check if there is a bounding box collision
        returns a boolean.
        """        
        # Render the Ikea object
        bpy.ops.object.select_all(action='DESELECT')
        obj2.select_set(True)
        obj2.location = obj1.location
        obj2.rotation_euler = obj1.rotation_euler
        if scale:
            obj2.scale = self._bb_ratio(obj1.bound_box, obj2.bound_box)

        # Check for collision between the ikea object and other objects in the scene
        intersection = False
        for obj in bpy.context.scene.objects: # for each object
            if obj.type == "MESH" and "ikea" not in obj:
                intersection  = check_bb_intersection(obj, obj2)
                if intersection:
                    break

        return not intersection

    def run(self):

        # Use a selector to get the list of ikea objects
        sel_objs = {}
        sel_objs['selector'] = self._ikea_objects_selector
        # create Config objects
        sel_conf = Config(sel_objs)
        ikea_objects = sel_conf.get_list("selector")

        # TODO: there should be a better way to do this once we support multiple conditions
        # Group Ikea objects by the category they replace
        ikea_objects_dict = defaultdict(list)
        for ikea_obj in ikea_objects:
            ikea_objects_dict[ikea_obj["replacing"]].append(ikea_obj)

        # Get objects in the scene that belongs to that category
        for category in ikea_objects_dict:
            ikea_category_list = ikea_objects_dict[category]

            # Use a selector to get objects to be replaced in the original scene
            sel_objs = {}
            self._ikea_objects_selector["condition"] = {"coarse_grained_class": category}
            sel_objs['selector'] = self._ikea_objects_selector

            # create Config objects
            sel_conf = Config(sel_objs)

            # invoke a Getter, get a list of objects to replace
            orginal_objects = sel_conf.get_list("selector")

            # Now we have two lists to do the switching between
            # Switch between a ratio of the objects in the scene with the list of the provided ikea objects randomly
            indices = np.random.choice(len(ikea_category_list), int(self._switch_ratio * len(orginal_objects)))

            for idx, ikea_idx in enumerate(indices):
                original_object = orginal_objects[idx]
                ikea_object = ikea_category_list[ikea_idx]
                if self._can_replace(original_object, ikea_object):
                    # Update the scene
                    original_object.hide_render = True
                    ikea_object.hide_render = False
                    bpy.context.view_layer.objects.active = ikea_object
                    bpy.context.view_layer.update()
                    ikea_object['category_id'] = original_object['category_id']
                    print('Switched', original_object.name, ' by an ikea object', ikea_object.name)       
                else:
                    bpy.context.view_layer.objects.active = original_object
                    bpy.context.view_layer.update()
                    print('Collision happened while replacing an object, falling back to original one.')
