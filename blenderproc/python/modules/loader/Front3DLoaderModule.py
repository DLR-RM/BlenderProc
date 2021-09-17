import os

from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.modules.main.GlobalStorage import GlobalStorage
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.utility.LabelIdMapping import LabelIdMapping
from blenderproc.python.utility.Utility import resolve_path, Utility, resolve_resource
from blenderproc.python.loader.Front3DLoader import load_front3d


class Front3DLoaderModule(LoaderInterface):
    """
    Loads the 3D-Front dataset.

    https://tianchi.aliyun.com/specials/promotion/alibaba-3d-scene-dataset

    Each object gets the name based on the category/type, on top of that you can use a mapping specified in the
    resources/front_3D folder.

    The dataset already supports semantic segmentation with either the 3D-Front classes or the nyu classes.
    As we have created this mapping ourselves it might be faulty.

    The Front3DLoader creates automatically lights in the scene, by adding emission shaders to the ceiling and lamps.
    The strength can be configured via the config.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - json_path
          - Path to the json file, where the house information is stored.
          - string
        * - 3D_future_model_path
          - Path to the models used in the 3D-Front dataset. Type: str
          - string
        * - 3D_front_texture_path
          - Path to the 3D-front-texture folder. Type: str
          - string
        * - mapping_file
          - Path to a file, which maps the names of the objects to ids. Default:
            resources/front_3D/3D_front_mapping.csv
          - string
        * - ceiling_light_strength
          - Strength of the emission shader used in the ceiling. Default: 0.8
          - float
        * - lamp_light_strength
          - Strength of the emission shader used in each lamp. Default: 7.0
          - float
   """

    def __init__(self, config: Config):
        LoaderInterface.__init__(self, config)

        self.mapping_file = resolve_path(self.config.get_string("mapping_file", resolve_resource(os.path.join("front_3D", "3D_front_mapping.csv"))))
        if not os.path.exists(self.mapping_file):
            raise Exception("The mapping file could not be found: {}".format(self.mapping_file))

    def run(self):
        label_mapping = LabelIdMapping.from_csv(self.mapping_file)
        # Add label mapping to global storage, s.t. it could be used for naming semantic segmentations.
        GlobalStorage.set("label_mapping", label_mapping)

        loaded_objects = load_front3d(
            json_path=self.config.get_string("json_path"),
            future_model_path=self.config.get_string("3D_future_model_path"),
            front_3D_texture_path=self.config.get_string("3D_front_texture_path"),
            label_mapping=label_mapping,
            ceiling_light_strength=self.config.get_float("ceiling_light_strength", 0.8),
            lamp_light_strength=self.config.get_float("lamp_light_strength", 7.0)
        )
        self._set_properties(loaded_objects)
