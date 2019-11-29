
import bpy

from src.loader.Loader import Loader
from src.main.Module import Module
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
        bpy.ops.import_scene.obj(filepath=Utility.resolve_path(self.config.get_string("path")))

        # Set the physics property of all imported objects
        self._set_physics_property(bpy.context.selected_objects)