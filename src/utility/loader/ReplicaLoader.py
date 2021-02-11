import os

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility


class ReplicaLoader(LoaderInterface):
    """ Just imports the objects for the given file path

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_path
          - The path to the data folder, where all rooms are saved.
          - string
        * - data_set_name
          - Name of the room (for example: apartment_0).
          - string
        * - use_ambient_occlusion
          - Use ambient occlusion to lighten up the scene, if the RgbRenderer is used. Default: False.
          - bool
        * - use_smooth_shading
          - Enable smooth shading on all surfaces, instead of flat shading. Default: False.
          - bool
    """
    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        """ Just imports the configured .ply file straight into blender for the replica case. """
        file_path = os.path.join(self.config.get_string('data_path'), self.config.get_string('data_set_name'), 'mesh.ply')
        loaded_objects = Utility.import_objects(file_path)

        # Set the physics property of all imported objects
        self._set_properties(loaded_objects)

        if self.config.get_bool('use_ambient_occlusion', False):
            bpy.context.scene.world.light_settings.use_ambient_occlusion = True  # turn AO on
            bpy.context.scene.world.light_settings.ao_factor = 0.9  # set it to 0.5

        if self.config.get_bool('use_smooth_shading', False):
            for poly in bpy.data.objects['mesh'].data.polygons:
                poly.use_smooth = True
