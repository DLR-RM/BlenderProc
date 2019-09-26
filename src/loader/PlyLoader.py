from src.main.Module import Module
import bpy

class PlyLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """Just imports the configured .ply file straight into blender

        The import will load all materials into cycle nodes.
        """
        bpy.ops.import_mesh.ply(filepath=self.config.get_string("path"))
        if self.config.get_bool('use_ambient_occlusion', False):
            bpy.context.scene.world.light_settings.use_ambient_occlusion = True  # turn AO on
            bpy.context.scene.world.light_settings.ao_factor = 0.5  # set it to 0.5
        if self.config.get_bool('use_smooth_shading', False):
            for poly in bpy.data.objects['mesh'].data.polygons:
                poly.use_smooth = True