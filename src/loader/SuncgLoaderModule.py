import os

from src.loader.LoaderInterface import LoaderInterface
from src.utility.LabelIdMapping import LabelIdMapping
from src.utility.Utility import Utility
from src.utility.loader.SuncgLoader import SuncgLoader


class SuncgLoaderModule(LoaderInterface):
    """ Loads a house.json file into blender.

     - Loads all objects files specified in the house.json file.
     - Orders them hierarchically (level -> room -> object)
     - Writes metadata into the custom properties of each object

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - path
          - The path to the house.json file which should be loaded.
          - string
        * - suncg_path
          - The path to the suncg root directory which should be used for loading objects, rooms, textures etc.
            Default: is extracted from the house.json path
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)
        self.house_path = Utility.resolve_path(self.config.get_string("path"))
        suncg_folder_path = os.path.join(os.path.dirname(self.house_path), "../..")
        self.suncg_dir = self.config.get_string("suncg_path", suncg_folder_path)

        LabelIdMapping.assign_mapping(Utility.resolve_path(os.path.join('resources', 'id_mappings', 'nyu_idset.csv')))

    def run(self):
        loaded_objects = SuncgLoader.load(self.house_path, self.suncg_dir)
        self._set_properties(loaded_objects)
