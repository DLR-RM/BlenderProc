import os
import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class PlyLoader(Loader):

    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        """Just imports the configured .ply file straight into blender

        """
        if not self.config.get_bool('is_replica_object', False):
            loaded_objects = Utility.import_objects(filepath=self.config.get_string("path"))
        else:
            file_path = os.path.join(self.config.get_string('data_path'), self.config.get_string('data_set_name'), 'mesh.ply')
            loaded_objects = Utility.import_objects(file_path)

        # Set the physics property of all imported objects
        self._set_physics_property(loaded_objects)

        if self.config.get_bool('use_ambient_occlusion', False):
            bpy.context.scene.world.light_settings.use_ambient_occlusion = True  # turn AO on
            bpy.context.scene.world.light_settings.ao_factor = 0.9  # set it to 0.5

        if self.config.get_bool('use_smooth_shading', False):
            for poly in bpy.data.objects['mesh'].data.polygons:
                poly.use_smooth = True
