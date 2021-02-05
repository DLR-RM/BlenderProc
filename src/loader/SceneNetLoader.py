import glob
import os
import random

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.LabelIdMapping import LabelIdMapping


class SceneNetLoader(LoaderInterface):
    """
    Loads all SceneNet objects at the given "file_path".

    The textures for each object are sampled based on the name of the object, if the name is not represented in the
    texture folder the unknown folder is used. This folder does not exists, after downloading the texture dataset.
    Make sure to create and put some textures, you want to use for these instances there.

    All objects get "category_id" set based on the data in the "resources/id_mappings/nyu_idset.csv"

    Each object will have the custom property "is_scene_net_obj".

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - file_path
          - The path to the .obj file from SceneNet.
          - string
        * - texture_folder
          - The path to the texture folder used to sample the textures.
          - string
        * - unknown_texture_folder
          - The path to the textures, which are used if the the texture type is unknown. The default path does not
            exist if the dataset was just downloaded, it has to be created manually. Default:
            ${texture_folder}/unknown
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

        self._file_path = Utility.resolve_path(self.config.get_string("file_path"))

        self._texture_folder = Utility.resolve_path(self.config.get_string("texture_folder"))

        # the default unknown texture folder is not included inside of the scenenet texture folder
        default_unknown_texture_folder = os.path.join(self._texture_folder, "unknown")
        # the textures in this folder are used, if the object has no available texture
        self._unknown_texture_folder = Utility.resolve_path(self.config.get_string("unknown_texture_folder",
                                                            default_unknown_texture_folder))

        LabelIdMapping.assign_mapping(Utility.resolve_path(os.path.join('resources', 
            'id_mappings', 'nyu_idset.csv')))

        if LabelIdMapping.label_id_map:
            bpy.context.scene.world["category_id"] = LabelIdMapping.label_id_map["void"]
        else:
            print("Warning: The category labeling file could not be found -> no semantic segmentation available!")


    def run(self):
        """
        Run the module, loads all the objects and set the properties correctly (including the category_id)
        """
        # load the objects (Use use_image_search=False as some image names have a "/" prefix which will lead to blender search the whole root directory recursively!
        loaded_objects = Utility.import_objects(filepath=self._file_path, use_image_search=False)
        loaded_objects.sort(key=lambda ele: ele.name)
        # sample materials for each object
        self._random_sample_materials_for_each_obj(loaded_objects)

        # set the category ids for each object
        self._set_category_ids(loaded_objects)

        for obj in loaded_objects:
            obj["is_scene_net_obj"] = True

        # add custom properties
        self._set_properties(loaded_objects)

    def _random_sample_materials_for_each_obj(self, loaded_objects):
        """
        Random sample materials for each of the loaded objects

        Based on the name the textures from the texture_folder will be selected

        :param loaded_objects: objects loaded from the .obj file
        """
        # for each object add a material
        for obj in loaded_objects:
            for mat_slot in obj.material_slots:
                material = mat_slot.material
                nodes = material.node_tree.nodes
                links = material.node_tree.links
                principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                texture_nodes = Utility.get_nodes_with_type(nodes, "ShaderNodeTexImage")
                if not texture_nodes or len(texture_nodes) == 1:
                    if len(texture_nodes) == 1:
                        # these materials do not exist they are just named in the .mtl files
                        texture_node = texture_nodes[0]
                    else:
                        texture_node = nodes.new("ShaderNodeTexImage")
                    mat_name = material.name
                    if "." in mat_name:
                        mat_name = mat_name[:mat_name.find(".")]
                    mat_name = mat_name.replace("_", "")
                    # remove all digits from the string
                    mat_name = ''.join([i for i in mat_name if not i.isdigit()])
                    image_paths = glob.glob(os.path.join(self._texture_folder, mat_name, "*"))
                    if not image_paths:
                        if not os.path.exists(self._unknown_texture_folder):
                            raise Exception("The unknown texture folder does not exist: {}, check if it was "
                                            "set correctly via the config.".format(self._unknown_texture_folder))

                        image_paths = glob.glob(os.path.join(self._unknown_texture_folder, "*"))
                        if not image_paths:
                            raise Exception("The unknown texture folder did not contain "
                                            "any textures: {}".format(self._unknown_texture_folder))
                    image_paths.sort()
                    image_path = random.choice(image_paths)
                    if os.path.exists(image_path):
                        texture_node.image = bpy.data.images.load(image_path, check_existing=True)
                    else:
                        raise Exception("No image was found for this entity: {}, "
                                        "material name: {}".format(obj.name, mat_name))
                    links.new(texture_node.outputs["Color"], principled_bsdf.inputs["Base Color"])
        for obj in loaded_objects:
            obj_name = obj.name
            if "." in obj_name:
                obj_name = obj_name[:obj_name.find(".")]
            obj_name = obj_name.lower()
            if "wall" in obj_name or "floor" in obj_name or "ceiling" in obj_name:
                # set the shading of all polygons to flat
                for poly in obj.data.polygons:
                    poly.use_smooth = False

    def _set_category_ids(self, loaded_objects):
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

        if LabelIdMapping.label_id_map:
            for obj in loaded_objects:
                obj_name = obj.name.lower().split(".")[0]

                # If it's one of the cases that the category have different names in both idsets.
                if obj_name in normalize_name:
                    obj_name = normalize_name[obj_name]  # Then normalize it.

                if obj_name in LabelIdMapping.label_id_map:
                    obj["category_id"] = LabelIdMapping.label_id_map[obj_name]
                # Check whether the object's name without suffixes like 's', '1' or '2' exist in the mapping.
                elif obj_name[:-1] in LabelIdMapping.label_id_map:
                    obj["category_id"] = LabelIdMapping.label_id_map[obj_name[:-1]]
                elif "painting" in obj_name:
                    obj["category_id"] = LabelIdMapping.label_id_map["picture"]
                else:
                    print("This object was not specified: {} use objects for it.".format(obj_name))
                    obj["category_id"] = LabelIdMapping.label_id_map["otherstructure".lower()]

                # Correct names of floor and ceiling objects to make them later easier to identify (e.g. by the FloorExtractor)
                if obj["category_id"] == LabelIdMapping.label_id_map["floor"]:
                    obj.name = "floor"
                elif obj["category_id"] == LabelIdMapping.label_id_map["ceiling"]:
                    obj.name = "ceiling"