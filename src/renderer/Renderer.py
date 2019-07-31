from src.main.Module import Module
import bpy
import os

from src.utility.Utility import Utility
import addon_utils


class Renderer(Module):

    def __init__(self, config):
        Module.__init__(self, config)
        addon_utils.enable("render_auto_tile_size")
        self.output_dir = Utility.resolve_path(self.config.get_string("output_dir"))

    def _configure_renderer(self):
        bpy.context.scene.cycles.samples = self.config.get_int("samples", 256)

        if self.config.get_bool("auto_tile_size", True):
            bpy.context.scene.ats_settings.is_enabled = True
        else:
            bpy.context.scene.ats_settings.is_enabled = False
            bpy.context.scene.render.tile_x = self.config.get_int("tile_x")
            bpy.context.scene.render.tile_y = self.config.get_int("tile_y")

        bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", 512)
        bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", 512)
        bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1)
        bpy.context.scene.render.resolution_percentage = 100

        # Lightning settings to reduce training time
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.render.layers[0].cycles.use_denoising = True

        simplify_subdivision_render = self.config.get_int("simplify_subdivision_render", 3)
        if simplify_subdivision_render > 0:
            bpy.context.scene.render.use_simplify = True
            bpy.context.scene.render.simplify_subdivision_render = simplify_subdivision_render

        bpy.context.scene.cycles.device = "GPU"
        bpy.context.scene.cycles.glossy_bounces = self.config.get_int("glossy_bounces", 0)
        bpy.context.scene.cycles.ao_bounces_render = self.config.get_int("ao_bounces_render", 3)
        bpy.context.scene.cycles.max_bounces = self.config.get_int("max_bounces", 3)
        bpy.context.scene.cycles.min_bounces = self.config.get_int("min_bounces", 1)
        bpy.context.scene.cycles.transmission_bounces = self.config.get_int("transmission_bounces", 0)
        bpy.context.scene.cycles.volume_bounces = self.config.get_int("volume_bounces", 0)

        bpy.context.scene.cycles.debug_bvh_type = "STATIC_BVH"
        bpy.context.scene.cycles.debug_use_spatial_splits = True
        bpy.context.scene.render.use_persistent_data = True

    def _render(self, default_prefix):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        bpy.context.scene.render.filepath = os.path.join(self.output_dir, self.config.get_string("output_file_prefix", default_prefix))
        bpy.ops.render.render(animation=True, write_still=True)

    def _register_output(self, default_prefix, default_key, suffix):
        # Store output path and configured key into the scene's custom properties
        output = {
            "key": self.config.get_string("output_key", default_key),
            "path": os.path.join(self.output_dir, self.config.get_string("output_file_prefix", default_prefix)) + "%04d" + suffix
        }

        if "output" in bpy.context.scene:
            bpy.context.scene["output"] += [output]
        else:
            bpy.context.scene["output"] = [output]
