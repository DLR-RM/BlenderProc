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
        bpy.ops.import_mesh.ply(filepath=self.config.get_string("path"))
        rotation_file_path = self.config.get_string('rotation_file_path', '')
        if len(rotation_file_path) > 0:
            if os.path.exists(rotation_file_path):
                rot_value = None
                with open(rotation_file_path, 'r') as data:
                    try:
                        rot_value = float(data.read().strip())
                    except ValueError:
                        print("Couldn't read rotation value in {}".format(rotation_file_path))
                if rot_value is not None:
                    bpy.ops.transform.rotate(value=radians(rot_value), orient_axis='Z')


            else:
                print("File does not exist {}:".format(rotation_file_path))
        if self.config.get_bool('use_ambient_occlusion', False):
            bpy.context.scene.world.light_settings.use_ambient_occlusion = True  # turn AO on
            bpy.context.scene.world.light_settings.ao_factor = 0.9  # set it to 0.5
        if self.config.get_bool('use_smooth_shading', False):
            for poly in bpy.data.objects['mesh'].data.polygons:
                poly.use_smooth = True