from src.main.Module import Module
import bpy

class ObjLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """Just imports the configured .obj file straight into blender

        The import will load all materials into cycle nodes.
        """
        bpy.ops.import_scene.obj(filepath=self.config.get_string("path"))
