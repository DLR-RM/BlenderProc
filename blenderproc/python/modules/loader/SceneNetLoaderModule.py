import os

from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.modules.main.GlobalStorage import GlobalStorage
from blenderproc.python.utility.LabelIdMapping import LabelIdMapping
from blenderproc.python.utility.Utility import resolve_path, Utility, resolve_resource
from blenderproc.python.loader.SceneNetLoader import load_scenenet


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

        self._file_path = resolve_path(self.config.get_string("file_path"))

        self._texture_folder = resolve_path(self.config.get_string("texture_folder"))

        # the default unknown texture folder is not included inside of the scenenet texture folder
        default_unknown_texture_folder = os.path.join(self._texture_folder, "unknown")
        # the textures in this folder are used, if the object has no available texture
        self._unknown_texture_folder = resolve_path(self.config.get_string("unknown_texture_folder",
                                                            default_unknown_texture_folder))



    def run(self):
        """
        Run the module, loads all the objects and set the properties correctly (including the category_id)
        """
        label_mapping = LabelIdMapping.from_csv(resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
        # Add label mapping to global storage, s.t. it could be used for naming semantic segmentations.
        GlobalStorage.set("label_mapping", label_mapping)
        # load the objects (Use use_image_search=False as some image names have a "/" prefix which will lead to blender search the whole root directory recursively!
        loaded_objects = load_scenenet(
            file_path=self._file_path,
            texture_folder=self._texture_folder,
            label_mapping=label_mapping,
            unknown_texture_folder=self._unknown_texture_folder
        )

        # add custom properties
        self._set_properties(loaded_objects)
