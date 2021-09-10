from blenderproc.python.modules.renderer.RendererInterface import RendererInterface
from blenderproc.python.material import MaterialLoaderUtility
import blenderproc.python.renderer.RendererUtility as RendererUtility
from blenderproc.python.utility.Utility import Utility


class RgbRenderer(RendererInterface):
    """
    Renders rgb images for each registered keypoint.

    Images are stored as PNG-files or JPEG-files with 8bit color depth.

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - render_texture_less
          - Render all objects with a white slightly glossy texture, does not change emission materials, Default:
            False.
          - bool
        * - image_type
          - Image type of saved rendered images, Default: 'PNG'. Available: ['PNG','JPEG']
          - str
        * - transparent_background
          - Whether to render the background as transparent or not, Default: False.
          - bool
        * - use_motion_blur
          - Use Blender motion blur feature which is required for motion blur and rolling shutter simulation. This
            feature only works if camera poses follow a continous trajectory as Blender performs a Bezier
            interpolation between keyframes and therefore arbitrary results are to be expected if camera poses are
            discontinuous (e.g. when sampled), Default: False
          - bool
        * - motion_blur_length
          - Motion blur effect length (in frames), Default: 0.1
          - float
        * - use_rolling_shutter
          - Use rolling shutter simulation (top to bottom). This depends on the setting enable_motion_blur being
            activated and a motion_blur_length > 0, Default: False
          - bool
        * - rolling_shutter_length
          - Time as fraction of the motion_blur_length one scanline is exposed when enable_rolling_shutter is
            activated. If set to 1, this creates a pure motion blur effect, if set to 0 a pure rolling shutter
            effect, Default: 0.2
          - float
    """
    def __init__(self, config):
        RendererInterface.__init__(self, config)
        self._texture_less_mode = config.get_bool('render_texture_less', False)
        self._image_type = config.get_string('image_type', 'PNG')
        self._use_motion_blur = config.get_bool('use_motion_blur', False)
        self._motion_blur_length = config.get_float('motion_blur_length', 0.1)
        self._use_rolling_shutter = config.get_bool('use_rolling_shutter', False)
        self._rolling_shutter_length = config.get_float('rolling_shutter_length', 0.2)


    def run(self):
        # if the rendering is not performed -> it is probably the debug case.
        do_undo = not self._avoid_output
        with Utility.UndoAfterExecution(perform_undo_op=do_undo):
            self._configure_renderer(use_denoiser=True, default_denoiser="Intel")

            # check if texture less render mode is active
            if self._texture_less_mode:
                MaterialLoaderUtility.change_to_texture_less_render(self._use_alpha_channel)

            if self._use_alpha_channel:
                MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=True)

            # motion blur
            if self._use_motion_blur:
                RendererUtility.enable_motion_blur(self._motion_blur_length, 'TOP' if self._use_rolling_shutter else "NONE", self._rolling_shutter_length)

            self._render(
                "rgb_",
                "colors",
                enable_transparency=self.config.get_bool("transparent_background", False),
                file_format=self._image_type
            )
