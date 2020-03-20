import bpy
import os

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class BlendCollectionLoader(Loader):
    """ Loads all collections from the .blend's file Collection section.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "Path to a .blend file. Type: string."
    """
    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        # get a path
        path = Utility.resolve_path(self.config.get_string("path"))
        # load all collections from a .blend file
        with bpy.data.libraries.load(path) as (data_from, data_to):
            for collection in data_from.collections:

                bpy.ops.wm.append(filepath=os.path.join(path, "/Collection", collection), filename=collection,
                                  directory=os.path.join(path + "/Collection"))
