import os
import random
import warnings
import numpy as np

import mathutils
import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.BlenderUtility import get_bounds

class IKEALoader(LoaderInterface):
    """
    This class loads objects from the IKEA dataset.

    Objects can be selected randomly, based on object type, object style, or both.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_dir
          - The directory with all the IKEA models. Default: 'resources/IKEA'
          - string
        * - obj_type
          - The category to use for example: 'bookcase'. Default: None. Available: ['bed', 'bookcase', 'chair',
            'desk', 'sofa', 'table', 'wardrobe']
          - string
        * - obj_style
          - The IKEA style to use for example: 'hemnes'. Default: None. See data_dir for other options.
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

        self._data_dir = Utility.resolve_path(self.config.get_string("data_dir", os.path.join("resources", "IKEA")))

        self._obj_dict = dict()
        self._generate_object_dict()

        if self.config.has_param("obj_type"):
            self._obj_type = self.config.get_raw_value("obj_type", None)
        else:
            self._obj_type = None
        if self.config.has_param("obj_style"):
            self._obj_style = self.config.get_raw_value("obj_style", None)
        else:
            self._obj_style = None

    def _generate_object_dict(self):
        """
        Generates a dictionary of all available objects, i.e. all .obj files that have an associated .mtl file.
        dict: {IKEA_<type>_<style> : [<path_to_obj_file>, ...]}
        """
        counter = 0
        for path, subdirs, files in os.walk(self._data_dir):
            for name in files:
                if '.obj' in name:
                    category = [s for s in path.split('/') if 'IKEA_' in s][0]
                    obj_path = os.path.join(path, name)
                    if self._check_material_file(obj_path):
                        self._obj_dict.setdefault(category, []).append(obj_path)
                        counter += 1
        print('Found {} object files in dataset belonging to {} categories'.format(counter, len(self._obj_dict)))
        if len(self._obj_dict) == 0:
            raise Exception("No obj file was found, check if the correct folder is provided!")

    @staticmethod
    def _check_material_file(path):
        """
        Checks whether there is a texture file (.mtl) associated to the object available.

        :param path: (str) path to object
        :return: (boolean) texture file exists
        """
        name = os.path.basename(path).split(".")[0]
        obj_dir = os.path.dirname(path)
        mtl_path = os.path.join(obj_dir, name + ".mtl")
        return os.path.exists(mtl_path)

    def _get_object_by_type(self, obj_type):
        """
        Finds all available objects with a specific type.

        :param obj_type: (str) type of object e.g. 'table'
        :return: (list) list of available objects with specified type
        """
        object_lst = [obj[0] for (key, obj) in self._obj_dict.items() if obj_type in key]
        if not object_lst:
            warnings.warn("There were no objects found matching the type: {}.".format(obj_type), category=Warning)
        return object_lst

    def _get_object_by_style(self, obj_style):
        """
        Finds all available objects with a specific style, i.e. IKEA product series.

        :param obj_type: (str) type of object e.g. 'table'
        :return: (list) list of available objects with specified style
        """
        object_lst = [obj[0] for (key, obj) in self._obj_dict.items() if obj_style in key.lower()]
        if not object_lst:
            warnings.warn("There were no objects found matching the style: {}.".format(obj_style), category=Warning)
        return object_lst

    def run(self):
        """
        Chooses objects based on selected type and style.
        If there are multiple options it picks one randomly or if style or type is None it picks one randomly.
        Loads the selected object via file path.
        """
        if self._obj_type is not None and self._obj_style is not None:
            object_lst = [obj[0] for (key, obj) in self._obj_dict.items() \
                          if self._obj_style in key.lower() and self._obj_type in key]
            if not object_lst:
                selected_obj = random.choice(self._obj_dict.get(random.choice(list(self._obj_dict.keys()))))
                warnings.warn("Could not find object of type: {}, and style: {}. Selecting random object...".format(
                    self._obj_type, self._obj_style), category=Warning)
            else:
                # Multiple objects with same type and style are possible: select randomly from list.
                selected_obj = random.choice(object_lst)
        elif self._obj_type is not None:
            object_lst = self._get_object_by_type(self._obj_type)
            selected_obj = random.choice(object_lst)
        elif self._obj_style is not None:
            object_lst = self._get_object_by_style(self._obj_style)
            selected_obj = random.choice(object_lst)
        else:
            random_key = random.choice(list(self._obj_dict.keys()))
            # One key can have multiple object files as value: select randomly from list.
            selected_obj = random.choice(self._obj_dict.get(random_key))

        print("Selected object: ", os.path.basename(selected_obj))
        loaded_obj = Utility.import_objects(selected_obj)
        self._set_properties(loaded_obj)

        # extract the file unit from the .obj file to convert every object to meters
        file_unit = ""
        with open(selected_obj, "r") as file:
            first_lines = [next(file) for x in range(5)]
            for line in first_lines:
                if "File units" in line:
                    file_unit = line.strip().split(" ")[-1]
                    if file_unit not in ["inches", "meters", "centimeters", "millimeters"]:
                        raise Exception("The file unit type could not be found, check the selected "
                                        "file: {}".format(selected_obj))
                    break

        for obj in loaded_obj:
            # convert all objects to meters
            if file_unit == "inches":
                scale = 0.0254
            elif file_unit == "centimeters":
                scale = 0.01
            elif file_unit == "millimeters":
                scale = 0.001
            elif file_unit == "meters":
                scale = 1.0
            else:
                raise Exception("The file unit type: {} is not defined".format(file_unit))
            if scale != 1.0:
                # scale object down
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.transform.resize(value=(scale, scale, scale))
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.context.view_layer.update()

            # move all object centers to the world origin and set the bounding box correctly
            bb = get_bounds(obj)
            bb_center = np.mean(bb, axis=0)
            bb_min_z_value = np.min(bb, axis=0)[2]
            obj.location -= mathutils.Vector([bb_center[0], bb_center[1], bb_min_z_value])
