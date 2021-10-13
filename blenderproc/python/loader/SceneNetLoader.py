import glob
import os
import random
from typing import List

import bpy

from blenderproc.python.utility.LabelIdMapping import LabelIdMapping
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.loader.ObjectLoader import load_obj


def load_scenenet(file_path: str, texture_folder: str, label_mapping: LabelIdMapping, unknown_texture_folder: str = None) -> List[MeshObject]:
    """ Loads all SceneNet objects at the given "file_path".

    The textures for each object are sampled based on the name of the object, if the name is not represented in the
    texture folder the unknown folder is used. This folder does not exists, after downloading the texture dataset.
    Make sure to create and put some textures, you want to use for these instances there.

    All objects get "category_id" set based on the data in the "resources/id_mappings/nyu_idset.csv"

    Each object will have the custom property "is_scene_net_obj".

    :param file_path: The path to the .obj file from SceneNet.
    :param texture_folder: The path to the texture folder used to sample the textures.
    :param unknown_texture_folder: The path to the textures, which are used if the the texture type is unknown. The default path does not
                                   exist if the dataset was just downloaded, it has to be created manually.
    :return: The list of loaded mesh objects.
    """
    if unknown_texture_folder is None:
        unknown_texture_folder = os.path.join(texture_folder, "unknown")

    # load the objects (Use use_image_search=False as some image names have a "/" prefix which will lead to blender search the whole root directory recursively!
    loaded_objects = load_obj(filepath=file_path, use_image_search=False)
    loaded_objects.sort(key=lambda ele: ele.get_name())
    # sample materials for each object
    SceneNetLoader._random_sample_materials_for_each_obj(loaded_objects, texture_folder, unknown_texture_folder)

    # set the category ids for each object
    SceneNetLoader._set_category_ids(loaded_objects, label_mapping)

    for obj in loaded_objects:
        obj.set_cp("is_scene_net_obj", True)

    return loaded_objects


class SceneNetLoader:

    @staticmethod
    def _random_sample_materials_for_each_obj(loaded_objects: List[MeshObject], texture_folder: str, unknown_texture_folder: str):
        """
        Random sample materials for each of the loaded objects

        Based on the name the textures from the texture_folder will be selected

        :param loaded_objects: objects loaded from the .obj file
        :param texture_folder: The path to the texture folder used to sample the textures.
        :param unknown_texture_folder: The path to the textures, which are used if the the texture type is unknown.
        """
        # for each object add a material
        for obj in loaded_objects:
            for material in obj.get_materials():
                if material is None:
                    continue
                principled_bsdf = material.get_the_one_node_with_type("BsdfPrincipled")
                texture_nodes = material.get_nodes_with_type("ShaderNodeTexImage")
                if not texture_nodes or len(texture_nodes) == 1:
                    if len(texture_nodes) == 1:
                        # these materials do not exist they are just named in the .mtl files
                        texture_node = texture_nodes[0]
                    else:
                        texture_node = material.new_node("ShaderNodeTexImage")
                    mat_name = material.get_name()
                    if "." in mat_name:
                        mat_name = mat_name[:mat_name.find(".")]
                    mat_name = mat_name.replace("_", "")
                    # remove all digits from the string
                    mat_name = ''.join([i for i in mat_name if not i.isdigit()])
                    image_paths = glob.glob(os.path.join(texture_folder, mat_name, "*"))
                    if not image_paths:
                        if not os.path.exists(unknown_texture_folder):
                            raise Exception("The unknown texture folder does not exist: {}, check if it was "
                                            "set correctly via the config.".format(unknown_texture_folder))

                        image_paths = glob.glob(os.path.join(unknown_texture_folder, "*"))
                        if not image_paths:
                            raise Exception("The unknown texture folder did not contain "
                                            "any textures: {}".format(unknown_texture_folder))
                    image_paths.sort()
                    image_path = random.choice(image_paths)
                    if os.path.exists(image_path):
                        texture_node.image = bpy.data.images.load(image_path, check_existing=True)
                    else:
                        raise Exception("No image was found for this entity: {}, "
                                        "material name: {}".format(obj.get_name(), mat_name))
                    material.link(texture_node.outputs["Color"], principled_bsdf.inputs["Base Color"])
        for obj in loaded_objects:
            obj_name = obj.get_name()
            if "." in obj_name:
                obj_name = obj_name[:obj_name.find(".")]
            obj_name = obj_name.lower()
            if "wall" in obj_name or "floor" in obj_name or "ceiling" in obj_name:
                # set the shading of all polygons to flat
                obj.set_shading_mode("FLAT")

    @staticmethod
    def _set_category_ids(loaded_objects: List[MeshObject], label_mapping: LabelIdMapping):
        """
        Set the category ids for the objs based on the .csv file loaded in LabelIdMapping

        Each object will have a custom property with a label, can be used by the SegMapRenderer.

        :param loaded_objects: objects loaded from the .obj file
        """

        #  Some category names in scenenet objects are written differently than in nyu_idset.csv
        normalize_name = {"floor-mat": "floor_mat", "refrigerator": "refridgerator", "shower-curtain": "shower_curtain", 
        "nightstand": "night_stand", "Other-structure": "otherstructure", "Other-furniture": "otherfurniture",
        "Other-prop": "otherprop", "floor_tiles_floor_tiles_0125": "floor", "ground": "floor", "floor_enclose": "floor", "floor_enclose2": "floor",
        "floor_base_object01_56": "floor", "walls1_line01_12": "wall", "room_skeleton": "wall", "ceilingwall": "ceiling"}

        for obj in loaded_objects:
            obj_name = obj.get_name().lower().split(".")[0]

            # If it's one of the cases that the category have different names in both idsets.
            if obj_name in normalize_name:
                obj_name = normalize_name[obj_name]  # Then normalize it.

            if label_mapping.has_label(obj_name):
                obj.set_cp("category_id", label_mapping.id_from_label(obj_name))
            # Check whether the object's name without suffixes like 's', '1' or '2' exist in the mapping.
            elif label_mapping.has_label(obj_name[:-1]):
                obj.set_cp("category_id", label_mapping.id_from_label(obj_name[:-1]))
            elif "painting" in obj_name:
                obj.set_cp("category_id", label_mapping.id_from_label("picture"))
            else:
                print("This object was not specified: {} use objects for it.".format(obj_name))
                obj.set_cp("category_id", label_mapping.id_from_label("otherstructure".lower()))

            # Correct names of floor and ceiling objects to make them later easier to identify (e.g. by the FloorExtractor)
            if obj.get_cp("category_id") == label_mapping.id_from_label("floor"):
                obj.set_name("floor")
            elif obj.get_cp("category_id") == label_mapping.id_from_label("ceiling"):
                obj.set_name("ceiling")
