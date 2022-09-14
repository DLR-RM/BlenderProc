"""Loads all ikea objects, beware that the ikea objects can no longer be downloaded."""

import glob
import os
import random
import warnings
from collections import OrderedDict
from typing import Union, List, Optional, Dict

import bpy

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.loader.ObjectLoader import load_obj


def load_ikea(data_dir: str = 'resources/IKEA', obj_categories: Optional[Union[List[str], str]] = None,
              obj_style: Optional[str] = None) -> List[MeshObject]:
    """ Loads ikea objects based on selected type and style.

    If there are multiple options it picks one randomly or if style or type is None it picks one randomly.

    :param data_dir: The directory with all the IKEA models.
    :param obj_categories: The category to use for example: 'bookcase'. This can also be a list of elements.
                           Available: ['bed', 'bookcase', 'chair', 'desk', 'sofa', 'table', 'wardrobe']
    :param obj_style: The IKEA style to use for example: 'hemnes'. See data_dir for other options.
    :return: The list of loaded mesh objects.
    """
    obj_dict = _IKEALoader.generate_object_dict(data_dir)

    # If obj_categories is given, make sure it is a list
    if obj_categories is not None and not isinstance(obj_categories, list):
        obj_categories = [obj_categories]

    if obj_categories is not None and obj_style is not None:
        object_lst = []
        for obj_category in obj_categories:
            object_lst.extend([obj[0] for (key, obj) in obj_dict.items() \
                               if obj_style in key.lower() and obj_category in key])
        if not object_lst:
            selected_obj = random.choice(obj_dict.get(random.choice(list(obj_dict.keys()))))
            warnings.warn(f"Could not find object of type: {obj_categories}, and style: "
                          f"{obj_style}. Selecting random object...", category=Warning)
        else:
            # Multiple objects with same type and style are possible: select randomly from list.
            selected_obj = random.choice(object_lst)
    elif obj_categories is not None:
        object_lst = []
        for obj_category in obj_categories:
            object_lst.extend(_IKEALoader.get_object_by_type(obj_category, obj_dict))
        selected_obj = random.choice(object_lst)
    elif obj_style is not None:
        object_lst = _IKEALoader.get_object_by_style(obj_style, obj_dict)
        selected_obj = random.choice(object_lst)
    else:
        random_key = random.choice(list(obj_dict.keys()))
        # One key can have multiple object files as value: select randomly from list.
        selected_obj = random.choice(obj_dict.get(random_key))

    print("Selected object: ", os.path.basename(selected_obj))
    loaded_obj = load_obj(selected_obj)

    # extract the name from the path:
    selected_dir_name = os.path.dirname(selected_obj)
    selected_name = ""
    if os.path.basename(selected_dir_name).startswith("IKEA_"):
        selected_name = os.path.basename(selected_dir_name)
    else:
        selected_dir_name = os.path.dirname(selected_dir_name)
        if os.path.basename(selected_dir_name).startswith("IKEA_"):
            selected_name = os.path.basename(selected_dir_name)
    if selected_name:
        for obj in loaded_obj:
            obj.set_name(selected_name)

    # extract the file unit from the .obj file to convert every object to meters
    file_unit = ""
    with open(selected_obj, "r", encoding="utf-8") as file:
        first_lines = [next(file) for x in range(5)]
        for line in first_lines:
            if "File units" in line:
                file_unit = line.strip().split(" ")[-1]
                if file_unit not in ["inches", "meters", "centimeters", "millimeters"]:
                    raise RuntimeError(f"The file unit type could not be found, check the selected "
                                       f"file: {selected_obj}")
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
            raise RuntimeError(f"The file unit type: {file_unit} is not defined")
        if scale != 1.0:
            # move all object centers to the world origin and set the bounding box correctly
            bpy.ops.object.select_all(action='DESELECT')
            obj.select()
            bpy.context.view_layer.objects.active = obj.blender_obj
            # scale object down
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.resize(value=(scale, scale, scale))
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

    # removes the x-axis rotation found in all ShapeNet objects, this is caused by importing .obj files
    # the object has the same pose as before, just that the rotation_euler is now [0, 0, 0]
    for obj in loaded_obj:
        obj.persist_transformation_into_mesh(location=False, rotation=True, scale=False)

    # move the origin of the object to the world origin and on top of the X-Y plane
    # makes it easier to place them later on, this does not change the `.location`
    for obj in loaded_obj:
        obj.move_origin_to_bottom_mean_point()
    bpy.ops.object.select_all(action='DESELECT')
    return loaded_obj


class _IKEALoader:
    """
    This class loads objects from the IKEA dataset.

    Objects can be selected randomly, based on object type, object style, or both.
    """

    @staticmethod
    def generate_object_dict(data_dir: str) -> Dict[str, List[str]]:
        """
        Generates a dictionary of all available objects, i.e. all .obj files that have an associated .mtl file.

        :param data_dir: The directory with all the IKEA models.
        :return: dict: {IKEA_<type>_<style> : [<path_to_obj_file>, ...]}
        """
        obj_dict = {}
        counter = 0
        obj_files = glob.glob(os.path.join(data_dir, "IKEA", "*", "*.obj"))
        # this will ensure that the call is deterministic
        obj_files.sort()
        for obj_file in obj_files:
            category = [s for s in obj_file.split('/') if 'IKEA_' in s][0]
            if _IKEALoader.check_material_file(obj_file):
                obj_dict.setdefault(category, []).append(obj_file)
                counter += 1

        print(f'Found {counter} object files in dataset belonging to {len(obj_dict)} categories')
        if not obj_dict:
            raise RuntimeError("No obj file was found, check if the correct folder is provided!")
        # to avoid randomness while accessing the dict
        obj_dict = OrderedDict(obj_dict)

        return obj_dict

    @staticmethod
    def check_material_file(path: str) -> bool:
        """
        Checks whether there is a texture file (.mtl) associated to the object available.

        :param path: path to object
        :return: texture file exists
        """
        name = os.path.basename(path).split(".")[0]
        obj_dir = os.path.dirname(path)
        mtl_path = os.path.join(obj_dir, name + ".mtl")
        return os.path.exists(mtl_path)

    @staticmethod
    def get_object_by_type(obj_type: str, obj_dict: Dict[str, List[str]]) -> List[str]:
        """
        Finds all available objects with a specific type.

        :param obj_type: type of object e.g. 'table'
        :param obj_dict: mapping of the style and type to the path {IKEA_<type>_<style> : [<path_to_obj_file>, ...]}
        :return: list of available objects with specified type
        """
        object_lst = [obj[0] for (key, obj) in obj_dict.items() if obj_type in key]
        if not object_lst:
            warnings.warn(f"There were no objects found matching the type: {obj_type}.", category=Warning)
        return object_lst

    @staticmethod
    def get_object_by_style(obj_style: str, obj_dict: Dict[str, List[str]]) -> List[str]:
        """
        Finds all available objects with a specific style, i.e. IKEA product series.

        :param obj_style: Style of the object
        :param obj_dict: mapping of the style and type to the path {IKEA_<type>_<style> : [<path_to_obj_file>, ...]}
        :return: (list) list of available objects with specified style
        """
        object_lst = [obj[0] for (key, obj) in obj_dict.items() if obj_style in key.lower()]
        if not object_lst:
            warnings.warn(f"There were no objects found matching the style: {obj_style}.", category=Warning)
        return object_lst
