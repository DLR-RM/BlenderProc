import os

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.LabelIdMapping import LabelIdMapping
from src.utility.Utility import Utility
from src.utility.loader.SceneNetLoader import SceneNetLoader


class SceneNetLoaderModule(LoaderInterface):
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
        loaded_objects = SceneNetLoader.load(file_path=self._file_path, texture_folder=self._texture_folder, unknown_texture_folder=self._unknown_texture_folder)

        # add custom properties
        self._set_properties(loaded_objects)
