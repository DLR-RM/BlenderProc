from src.main.Module import Module
import bpy
import os

from src.utility.Utility import Utility


class Renderer(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def _configure_renderer(self):
        self.scene.cycles.samples = 256
        self.scene.render.tile_x = 256
        self.scene.render.tile_y = 256
        self.scene.render.resolution_x = 512
        self.scene.render.resolution_y = 512
        self.scene.render.pixel_aspect_x = (640.0 / 480)
        self.scene.render.resolution_percentage = 100

        # Lightning settings to reduce training time
        self.scene.render.engine = 'CYCLES'
        self.scene.render.layers[0].cycles.use_denoising = True
        self.scene.render.use_simplify = True
        self.scene.render.simplify_subdivision_render = 3
        self.scene.cycles.device = "GPU"
        self.scene.cycles.glossy_bounces = 0
        self.scene.cycles.ao_bounces_render = 3
        self.scene.cycles.max_bounces = 3
        self.scene.cycles.min_bounces = 1
        self.scene.cycles.transmission_bounces = 0
        self.scene.cycles.volume_bounces = 0
        self.scene.cycles.debug_bvh_type = "STATIC_BVH"
        self.scene.cycles.debug_use_spatial_splits = True
        self.scene.render.use_persistent_data = True

    def _render(self, default_prefix):
        output_dir = Utility.resolve_path(self.config.get_string("output_dir"))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.scene.render.filepath = os.path.join(output_dir, self.config.get_string("output_file_prefix", default_prefix))
        bpy.ops.render.render(animation=True, write_still=True)