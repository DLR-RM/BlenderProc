
import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class ObjLoader(Loader):
    """ Just imports the configured .obj file straight into blender

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "The path to the .obj file to load."
    """
    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        loaded_objects = Utility.import_objects(filepath=Utility.resolve_path(self.config.get_string("path")))

        # Set the physics property of all imported objects
        self._set_physics_property(loaded_objects)