from src.main.Module import Module
import bpy

class PlyLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """Just imports the configured .ply file straight into blender

        """
        bpy.ops.import_mesh.ply(filepath=self.config.get_string("path"))
