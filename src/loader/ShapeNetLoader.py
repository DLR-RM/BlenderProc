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
        self._used_synset_id = self.config.get_string("used_synset_id")

        taxonomy_file_path = os.path.join(self._data_path, "taxonomy.json")
        self._files_with_fitting_synset = ShapeNetLoader.get_files_with_synset(self._used_synset_id, taxonomy_file_path,
                                                                               self._data_path)

    @staticmethod
    def get_files_with_synset(used_synset_id, path_to_taxonomy_file, data_path):
        """
        Returns a list of a .obj file for the given synset_id
        :param used_synset_id: the id of the category something like: '02691156', see the data_path folder for more ids
        :param path_to_taxonomy_file: path to the taxonomy.json file, should be in the data_path, too
        :param data_path: path to the ShapeNetCore.v2 folder
        :return: list of .obj files, which are in the synset_id folder, based on the given taxonomy
        """
        if os.path.exists(path_to_taxonomy_file):
            files = []
            with open(path_to_taxonomy_file, "r") as f:
                loaded_data = json.load(f)
                for block in loaded_data:
                    if "synsetId" in block:
                        synset_id = block["synsetId"]
                        if synset_id == used_synset_id or used_synset_id in block["children"]:
                            id_path = os.path.join(data_path, synset_id)
                            files.extend(glob.glob(os.path.join(id_path, "*", "models", "*.obj")))
            return files
        else:
            raise Exception("The taxonomy file could not be found: {}".format(path_to_taxonomy_file))

    def run(self):
        selected_obj = random.choice(self._files_with_fitting_synset)
        loaded_obj = Utility.import_objects(selected_obj)
        self._set_properties(loaded_obj)

