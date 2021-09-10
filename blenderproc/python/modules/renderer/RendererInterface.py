import addon_utils
import bpy

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.utility.Config import Config
import blenderproc.python.renderer.RendererUtility as RendererUtility


class RendererInterface(Module):
    """
    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - output_file_prefix
          - The file prefix that should be used when writing the rendering to file.
          - String
        * - output_key
          - The key which should be used for storing the rendering in a merged file. which should be used for
            storing the rendering in a merged file.
          - String
        * - samples
          - Number of samples to render for each pixel. Higher numbers take longer but remove noise in dark areas.
            Default: 256, (not true for all Renderes).
          - int
        * - use_adaptive_sampling
          - Combined with the maximum sample amount, it is also possible to set the amount of noise left per pixel.
            This means pixel is sampled until the noise level is smaller than specified or the maximum amount of
            samples were reached. Do not use this with Non-RGB-Renders! Only used if specified" in config. Default: 0.0
          - float
        * - auto_tile_size
          - If true, then the number of render tiles is set automatically using the render_auto_tile_size addon.
            Default: True.
          - bool
        * - tile_x
          - The number of separate render tiles to use along the x-axis. Ignored if auto_tile_size is set to true. 
          - int
        * - tile_y
          - The number of separate render tiles to use along the y-axis. Ignored if auto_tile_size is set to true. 
          - int
        * - simplify_subdivision_render
          - Global maximum subdivision level during rendering. Speeds up rendering. Default: 3
          - int
        * - denoiser
          - The denoiser to use. Set to "Blender", if the Blender's built-in denoiser should be used or set to
            "Intel", if you want to use the Intel Open Image Denoiser, performs much better. Default: "Intel"
            Available: ["Intel", "Blender"].
          - string
        * - max_bounces
          - Total maximum number of bounces. Default: 3
          - int
        * - diffuse_bounces
          - Maximum number of diffuse reflection bounces, bounded by total maximum. Default: 3
          - int
        * - glossy_bounces
          - Maximum number of glossy reflection bounces, bounded by total maximum. Be careful the default is set to
            zero to improve rendering time, but it removes all indirect glossy rays from the rendering process.
            Default: 0
          - int
        * - ao_bounces_render
          - Approximate indirect light with background tinted ambient occlusion at the specified bounce. Default: 3
          - int
        * - transmission_bounces
          - Maximum number of transmission bounces, bounded by total maximum. Be careful the default is set to zero
            to improve rendering time, but it removes all indirect transmission rays from the rendering process.
            Default: 0
          - int
        * - transparency_bounces
          - Maximum number of transparency bounces, bounded by total maximum. A higher value helps if a lot of
            transparency objects are stacked after each other. Default: 8
          - int
        * - volume_bounces
          - Maximum number of volumetric scattering events. Default: 0
          - int
        * - render_distance
          - If true, the distance is also rendered to file. Default: False.
          - bool
        * - distance_output_file_prefix
          - The file prefix that should be used when writing distance to file. Default: `"distance_"`
          - string
        * - distance_output_key
          - The key which should be used for storing the distance in a merged file. Default: `"distance"`.
          - string
        * - distance_start
          - Starting distance of the distance, measured from the camera. Default: 0.1
          - float
        * - distance_range
          - Total distance in which the distance is measured. distance_end = distance_start + distance_range.
            Default: 25.0
          - float
        * - distance_falloff
          - Type of transition used to fade distance. Default: "Linear". Available: [LINEAR, QUADRATIC,
            INVERSE_QUADRATIC]
          - string
        * - render_depth
          - If true, the z-buffer is also rendered to file. Default: False.
          - bool
        * - depth_output_file_prefix
          - The file prefix that should be used when writing depth to file. Default: `"depth_"`
          - string
        * - depth_output_key
          - The key which should be used for storing the depth in a merged file. Default: `"depth"`.
          - string
        * - use_alpha
          - If true, the alpha channel stored in .png textures is used. Default: False
          - bool
        * - stereo
          - If true, renders a pair of stereoscopic images for each camera position. Default: False
          - bool
        * - cpu_threads
          - Set number of cpu cores used for rendering (1 thread is always used for coordination if more than one
            cpu thread means GPU-only rendering). When 0 is set, the number of threads will be set automatically. Default: 0
          - int
        * - render_normals
          - If true, the normals are also rendered. Default: False
          - bool
        * - normals_output_file_prefix
          - The file prefix that should be used when writing normals. Default: `"normals_"`
          - string
        * - normals_output_key
          - The key which is used for storing the normal in a merged file. Default: `"normal"`
          - string
        * - render_diffuse_color
          - If true, the diffuse color image are also rendered. Default: False
          - bool
    """

    def __init__(self, config: Config):
        Module.__init__(self, config)
        addon_utils.enable("render_auto_tile_size")

    def _configure_renderer(self, default_samples: int = 256, use_denoiser: bool = False,
                            default_denoiser: str = "Intel"):
        """
        Sets many different render parameters which can be adjusted via the config.

        :param default_samples: Default number of samples to render for each pixel
        :param use_denoiser: If true, a denoiser is used, only use this on color information
        :param default_denoiser: Either "Intel" or "Blender", "Intel" performs much better in most cases
        """
        RendererUtility._render_init()
        RendererUtility.set_samples(self.config.get_int("samples", default_samples))

        if self.config.has_param("use_adaptive_sampling"):
            RendererUtility.set_adaptive_sampling(self.config.get_float("use_adaptive_sampling"))

        if self.config.get_bool("auto_tile_size", True):
            RendererUtility.toggle_auto_tile_size(True)
        else:
            RendererUtility.toggle_auto_tile_size(False)
            RendererUtility.set_tile_size(self.config.get_int("tile_x"), self.config.get_int("tile_y"))

        # Set number of cpu cores used for rendering (1 thread is always used for coordination => 1
        # cpu thread means GPU-only rendering)
        RendererUtility.set_cpu_threads(self.config.get_int("cpu_threads", 0))
        
        print('Resolution: {}, {}'.format(bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y))

        RendererUtility.set_denoiser(None if not use_denoiser else self.config.get_string("denoiser", default_denoiser))

        RendererUtility.set_simplify_subdivision_render(self.config.get_int("simplify_subdivision_render", 3))

        RendererUtility.set_light_bounces(self.config.get_int("diffuse_bounces", 3),
                                          self.config.get_int("glossy_bounces", 0),
                                          self.config.get_int("ao_bounces_render", 3),
                                          self.config.get_int("max_bounces", 3),
                                          self.config.get_int("transmission_bounces", 0),
                                          self.config.get_int("transparency_bounces", 8),
                                          self.config.get_int("volume_bounces", 0))

        RendererUtility.toggle_stereo(self.config.get_bool("stereo", False))

        self._use_alpha_channel = self.config.get_bool('use_alpha', False)

    def _render(self, default_prefix: str, default_key: str, output_key_parameter_name: str = "output_key",
                output_file_prefix_parameter_name: str = "output_file_prefix", enable_transparency: bool = False,
                file_format: str = "PNG"):
        """ Renders each registered keypoint.

        :param default_prefix: The default prefix of the output files.
        """
        if self.config.get_bool("render_distance", False):
            RendererUtility.enable_distance_output(
                self._determine_output_dir(),
                self.config.get_string("distance_output_file_prefix", "distance_"),
                self.config.get_string("distance_output_key", "distance"),
                self.config.get_float("distance_start", 0.1),
                self.config.get_float("distance_range", 25.0),
                self.config.get_string("distance_falloff", "LINEAR")
            )

        if self.config.get_bool("render_depth", False):
            RendererUtility.enable_depth_output(
                self._determine_output_dir(),
                self.config.get_string("depth_output_file_prefix", "depth_"),
                self.config.get_string("depth_output_key", "depth")
            )

        if self.config.get_bool("render_normals", False):
            RendererUtility.enable_normals_output(
                self._determine_output_dir(),
                self.config.get_string("normals_output_file_prefix", "normals_"),
                self.config.get_string("normals_output_key", "normals")
            )

        if self.config.get_bool("render_diffuse_color", False):
            RendererUtility.enable_diffuse_color_output(
                self._determine_output_dir(),
                self.config.get_string("diffuse_color_output_file_prefix", "diffuse_"),
                self.config.get_string("diffuse_color_output_key", "diffuse")
            )

        RendererUtility.set_output_format(file_format, enable_transparency=enable_transparency)
        if not self._avoid_output:
            RendererUtility.render(
                self._determine_output_dir(),
                self.config.get_string(output_file_prefix_parameter_name, default_prefix),
                self.config.get_string(output_key_parameter_name, default_key),
                return_data=False
            )
