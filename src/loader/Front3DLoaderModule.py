import os

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Config import Config
from src.utility.LabelIdMapping import LabelIdMapping
from src.utility.Utility import Utility
from src.utility.loader.Front3DLoader import Front3DLoader


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
          - Path to the models used in the 3D-Front dataset. to the models used in the 3D-Front dataset. Type: str
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

        self.mapping_file = Utility.resolve_path(self.config.get_string("mapping_file", os.path.join("resources", "front_3D", "3D_front_mapping.csv")))
        if not os.path.exists(self.mapping_file):
            raise Exception("The mapping file could not be found: {}".format(self.mapping_file))
        _, self.mapping = LabelIdMapping.read_csv_mapping(self.mapping_file)

    def run(self):
        Front3DLoader.load(
            json_path=self.config.get_string("json_path"),
            future_model_path=self.config.get_string("3D_future_model_path"),
            mapping=self.mapping,
            ceiling_light_strength=self.config.get_float("ceiling_light_strength", 0.8),
            lamp_light_strength=self.config.get_float("lamp_light_strength", 7.0)
        )