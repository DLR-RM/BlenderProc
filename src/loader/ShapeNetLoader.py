import os
import random

import json
import glob

from src.loader.Loader import Loader
from src.utility.Utility import Utility

class ShapeNetLoader(Loader):

    def __init__(self, config):
        Loader.__init__(self, config)

        self._data_path = Utility.resolve_path(self.config.get_string("data_path"))
        taxonomy_file_path = os.path.join(self._data_path, "taxonomy.json")
        self._used_synsetId = self.config.get_string("used_synsetId")



        self._files_with_fitting_synset = self._get_files_with_synset(taxonomy_file_path)



    def _get_files_with_synset(self, path_to_taxonomy_file):
        if os.path.exists(path_to_taxonomy_file):
            files = []
            with open(path_to_taxonomy_file, "r") as f:
                loaded_data = json.load(f)
                for block in loaded_data:
                    if "name" in block:
                        id = block["synsetId"]
                        if id == self._used_synsetId or self._used_synsetId in block["children"]:
                            id_path = os.path.join(self._data_path, id)
                            files.extend(glob.glob(os.path.join(id_path, "*", "models", "*.obj")))
            return files
        else:
            raise Exception("The taxonomy file could not be found: {}".format(path_to_taxonomy_file))

    def run(self):
        selected_obj = random.choice(self._files_with_fitting_synset)
        loaded_obj = Utility.import_objects(selected_obj)
        self._set_properties(loaded_obj)

