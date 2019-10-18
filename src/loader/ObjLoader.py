from src.main.Module import Module
import bpy

class ObjLoader(Module):
    """ Just imports the configured .obj file straight into blender

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "The path to the .obj file to load."
    """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        bpy.ops.import_scene.obj(filepath=self.config.get_string("path"))
