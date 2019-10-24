from src.main.Module import Module
import bpy
import mathutils
import os
from math import radians

class PlyLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """Just imports the configured .ply file straight into blender

        """
        if not self.config.get_bool('is_replica_object', False):
            bpy.ops.import_mesh.ply(filepath=self.config.get_string("path"))
        else:
            file_path = os.path.join(self.config.get_string('data_path'), self.config.get_string('data_set_name'), 'mesh.ply')
            if os.path.exists(file_path):
                bpy.ops.import_mesh.ply(filepath=file_path)
            else:
                raise Exception("The filepath is not known: {}".format(file_path))
        if self.config.get_bool('use_ambient_occlusion', False):
            bpy.context.scene.world.light_settings.use_ambient_occlusion = True  # turn AO on
            bpy.context.scene.world.light_settings.ao_factor = 0.9  # set it to 0.5
        if self.config.get_bool('use_smooth_shading', False):
            for poly in bpy.data.objects['mesh'].data.polygons:
                poly.use_smooth = True