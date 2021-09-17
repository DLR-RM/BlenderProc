import os

from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.modules.main.GlobalStorage import GlobalStorage
from blenderproc.python.utility.LabelIdMapping import LabelIdMapping
from blenderproc.python.utility.Utility import resolve_path, Utility, resolve_resource
from blenderproc.python.loader.SuncgLoader import load_suncg


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
        self.house_path = resolve_path(self.config.get_string("path"))
        suncg_folder_path = os.path.join(os.path.dirname(self.house_path), "../..")
        self.suncg_dir = self.config.get_string("suncg_path", suncg_folder_path)

    def run(self):
        label_mapping = LabelIdMapping.from_csv(resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
        # Add label mapping to global storage, s.t. it could be used for naming semantic segmentations.
        GlobalStorage.set("label_mapping", label_mapping)

        loaded_objects = load_suncg(self.house_path, label_mapping, self.suncg_dir)
        self._set_properties(loaded_objects)
