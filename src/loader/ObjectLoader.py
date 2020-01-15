
import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class ObjectLoader(Loader):
    """ Just imports the objects for the given file path

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "The path to the 3D data file to load."
    """
    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        file_path = Utility.resolve_path(self.config.get_string("path"))
        loaded_objects = Utility.import_objects(filepath=file_path)

        # Set the physics property of all imported objects
        self._set_physics_property(loaded_objects)