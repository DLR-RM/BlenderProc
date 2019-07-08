from src.main.Module import Module
import bpy

class ObjLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        # Import obj (the import will convert all materials to cycle nodes
        bpy.ops.import_scene.obj(filepath=self.config.get_string("path"))
