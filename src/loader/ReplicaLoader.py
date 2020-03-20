import os
import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class ReplicaLoader(Loader):
    """ Just imports the objects for the given file path

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "data_path", "The path to the data folder, where all rooms are saved."
       "data_set_name", "Name of the room (for example: apartment_0)"
       "use_ambient_occlusion", "Use ambient occlusion to lighten up the scene, if the RgbRenderer is used."
       "use_smooth_shading", "Enable smooth shading on all surfaces, instead of flat shading"
    """
    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        """Just imports the configured .ply file straight into blender for the replica case

        """
        file_path = os.path.join(self.config.get_string('data_path'), self.config.get_string('data_set_name'), 'mesh.ply')
        loaded_objects = Utility.import_objects(file_path)

        # Set the physics property of all imported objects
        self._set_properties(loaded_objects)

        # add a default material to all imported objects
        mat = bpy.data.materials.new(name="ReplicaMaterial")
        mat.use_nodes = True
        for obj in loaded_objects:
            obj.data.materials.append(mat)

        if self.config.get_bool('use_ambient_occlusion', False):
            bpy.context.scene.world.light_settings.use_ambient_occlusion = True  # turn AO on
            bpy.context.scene.world.light_settings.ao_factor = 0.9  # set it to 0.5

        if self.config.get_bool('use_smooth_shading', False):
            for poly in bpy.data.objects['mesh'].data.polygons:
                poly.use_smooth = True
