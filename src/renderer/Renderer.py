from src.main.Module import Module
import bpy
import os

import addon_utils


class Renderer(Module):
    """
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "output_file_prefix", "The file prefix that should be used when writing the rendering to file."
       "output_key", "The key which should be used for storing the rendering in a merged file."

       "auto_tile_size", "If true, then the number of render tiles is set automatically using the render_auto_tile_size addon."
       "tile_x", "The number of separate render tiles to use along the x-axis. Ignored if auto_tile_size is set to true."
       "tile_y", "The number of separate render tiles to use along the y-axis. Ignored if auto_tile_size is set to true."
       "resolution_x", "The render image width."
       "resolution_y", "The render image height."
       "pixel_aspect_x", "The aspect ratio to use for the camera viewport. Can be different from the resolution aspect ratio to distort the image."
       "simplify_subdivision_render", "Global maximum subdivision level during rendering. Speeds up rendering."

       "samples", "Number of samples to render for each pixel."
       "max_bounces", "Total maximum number of bounces."
       "min_bounces", "Total minimum number of bounces."
       "glossy_bounces", "Maximum number of glossy reflection bounces, bounded by total maximum."
       "ao_bounces_render", "Approximate indirect light with background tinted ambient occlusion at the specified bounce."
       "transmission_bounces", "Maximum number of transmission bounces, bounded by total maximum."
       "volume_bounces", "Maximum number of volumetric scattering events"

       "render_depth", "If true, the depth is also rendered to file."
       "depth_output_file_prefix", "The file prefix that should be used when writing depth to file."
       "depth_output_key", "The key which should be used for storing the depth in a merged file."

       "stereo", "If true, renders a pair of stereoscopic images for each camera position."
    """
    def __init__(self, config):
        Module.__init__(self, config)
        addon_utils.enable("render_auto_tile_size")

    def _configure_renderer(self):
        """ Sets many different render parameters which can be adjusted via the config. """
        bpy.context.scene.cycles.samples = self.config.get_int("samples", 256)

        if self.config.get_bool("auto_tile_size", True):
            bpy.context.scene.ats_settings.is_enabled = True
        else:
            bpy.context.scene.ats_settings.is_enabled = False
            bpy.context.scene.render.tile_x = self.config.get_int("tile_x")
            bpy.context.scene.render.tile_y = self.config.get_int("tile_y")

        # Set number of cpu cores used for rendering (1 thread is always used for coordination => 1 cpu thread means GPU-only rendering)
        number_of_threads = self.config.get_int("cpu_threads", 1)
        # If set to 0, use number of cores (default)
        if number_of_threads > 0:
            bpy.context.scene.render.threads_mode = "FIXED"
            bpy.context.scene.render.threads = number_of_threads

        bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", 512)
        bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", 512)
        bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1)
        bpy.context.scene.render.resolution_percentage = 100

        # Lightning settings to reduce training time
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.view_layer.cycles.use_denoising = True

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
        # Setting use_persistent_data to True makes the rendering getting slower and slower (probably a blender bug)
        bpy.context.scene.render.use_persistent_data = False

        # Enable Stereoscopy
        bpy.context.scene.render.use_multiview = self.config.get_bool("stereo", False)
        if bpy.context.scene.render.use_multiview:
            bpy.context.scene.render.views_format = "STEREO_3D"

    def _write_depth_to_file(self):
        """ Configures the renderer, s.t. the z-values computed for the next rendering are directly written to file. """
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        bpy.context.view_layer.use_pass_z = True
        tree = bpy.context.scene.node_tree
        links = tree.links

        # Create a render layer
        rl = tree.nodes.new('CompositorNodeRLayers')      

        output_file = tree.nodes.new("CompositorNodeOutputFile")
        output_file.base_path = self.output_dir
        output_file.format.file_format = "OPEN_EXR"
        output_file.file_slots.values()[0].path = self.config.get_string("depth_output_file_prefix", "depth_")

        # Feed the Z output of the render layer to the input of the file IO layer
        links.new(rl.outputs[2], output_file.inputs['Image'])

    def _render(self, default_prefix):
        """ Renders each registered keypoint.

        :param default_prefix: The default prefix of the output files.
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        if self.config.get_bool("render_depth", False):
            self._write_depth_to_file()

        bpy.context.scene.render.filepath = os.path.join(self.output_dir, self.config.get_string("output_file_prefix", default_prefix))
        bpy.ops.render.render(animation=True, write_still=True)

    def _register_output(self, default_prefix, default_key, suffix, version):
        """ Registers new output type using configured key and file prefix.

        If depth rendering is enabled, this will also register the corresponding depth output type.

        :param default_prefix: The default prefix of the generated files.
        :param default_key: The default key which should be used for storing the output in merged file.
        :param suffix: The suffix of the generated files.
        :param version: The version number which will be stored at key_version in the final merged file.
        """
        use_stereo = self.config.get_bool("stereo", False)

        super(Renderer, self)._register_output(default_prefix, default_key, suffix, version, use_stereo)

        if self.config.get_bool("render_depth", False):
            self._add_output_entry({
                "key": self.config.get_string("depth_output_key", "depth"),
                "path": os.path.join(self.output_dir, self.config.get_string("depth_output_file_prefix", "depth_")) + "%04d" + ".exr",
                "version": "2.0.0",
                "stereo": use_stereo
            })


