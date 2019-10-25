from src.main.Module import Module
import bpy
import os

class PlyLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """Just imports the configured .ply file straight into blender
        """
        path = self.config.get_string("path")
        for fname in os.listdir(path):
            if fname.endswith(".ply"):
                bpy.ops.import_mesh.ply(filepath=os.path.join(path, fname))