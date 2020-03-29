import bpy
import os
import re

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class BlendLoader(Loader):
    """ Loads entities from a specified .blend file's section/datablock.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "Path to a .blend file. Type: string."
       "load_from", "Name of the datablock/folder inside .blend file. Type: string. See known_datablock_names for supported folder names/type IDs."
       "entities", "Regular expression representing a name pattern of entities' names. Optional. Type: string."
    """

    def __init__(self, config):
        Loader.__init__(self, config)
        # supported pairs of {datablock parameter names: ID type/section names}
        self.known_datablock_names = {"cameras": "/Camera",
                                      "collections": "/Collection",
                                      "images": "/Image",
                                      "lights": "/Light",
                                      "materials": "/Material",
                                      "meshes": "/Mesh",
                                      "objects": "/Object",
                                      "textures": "/Texture"}

    def run(self):
        # get a path to a .blend file
        path = Utility.resolve_path(self.config.get_string("path"))
        # get section name/Blend ID
        load_from = self.config.get_string("load_from")
        # get a entities' name regex if present, set to None if not
        if self.config.has_param("entities"):
            entities = self.config.get_string("entities")
        else:
            entities = None

        with bpy.data.libraries.load(path) as (data_from, data_to):
            # check if defined ID is supported
            if load_from in self.known_datablock_names.keys():
                # if some regex was specified, get corresponding matching entity's names
                if entities is not None:
                    entities_to_load = [item for item in getattr(data_from, load_from)
                                        if re.fullmatch(entities, item) is not None]
                # get all entity's names if not
                else:
                    entities_to_load = getattr(data_from, load_from)
                # load entities
                for entity_to_load in entities_to_load:
                    bpy.ops.wm.append(filepath=os.path.join(path, self.known_datablock_names[load_from], entity_to_load),
                                      filename=entity_to_load,
                                      directory=os.path.join(path + self.known_datablock_names[load_from]))
            else:
                raise Exception("Unsupported datablock parameter name: " + load_from +
                                ".\nSupported names: " + str(self.known_datablock_names.keys()) +
                                ".\n All possible names: " + str(dir(data_from)) +
                                "\n. If your ID exists, but not supported, please append a new pair of"
                                "{parameter name: type ID(folder name)} to the 'known_datablock_names' dict.")
