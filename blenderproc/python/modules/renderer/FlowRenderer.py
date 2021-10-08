from blenderproc.python.modules.renderer.RendererInterface import RendererInterface
from blenderproc.python.renderer.FlowRendererUtility import render_optical_flow
from blenderproc.python.utility.Utility import Utility


class FlowRenderer(RendererInterface):
    """ Renders optical flow between consecutive keypoints.

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - forward_flow_output_key
          - The key which should be used for storing forward optical flow values. Default: `"forward_flow"`.
          - string
        * - backward_flow_output_key
          - The key which should be used for storing backward optical flow values. Default: `"backward_flow"`.
          - string
        * - forward_flow
          - Whether to render forward optical flow. Default: True.
          - bool
        * - backward_flow
          - Whether to render backward optical flow. Default: True.
          - bool
        * - blender_image_coordinate_style
          - Whether to specify the image coordinate system at the bottom left (blender default; True) or top left
            (standard convention; False). Default: False
          - bool
        * - forward_flow_output_file_prefix
          - The file prefix that should be used when writing forward flow to a file. Default: `"forward_flow_"`
          - string
        * - backward_flow_output_file_prefix
          - The file prefix that should be used when writing backward flow to a file. Default: `"backward_flow_"`
          - string
        * - samples
          - The amount of samples rendered, this value should be 1. Only change it when you know what you are doing.
            Default: 1
          - int
    """

    def __init__(self, config):
        RendererInterface.__init__(self, config)

    def run(self):
        with Utility.UndoAfterExecution():
            self._configure_renderer(default_samples=1)

            if not self._avoid_output:
                render_optical_flow(
                    self._determine_output_dir(),
                    self._temp_dir,
                    self.config.get_bool('forward_flow', False),
                    self.config.get_bool('backward_flow', False),
                    self.config.get_bool('blender_image_coordinate_style', False),
                    self.config.get_string('forward_flow_output_file_prefix', 'forward_flow_'),
                    self.config.get_string("forward_flow_output_key", "forward_flow"),
                    self.config.get_string('backward_flow_output_file_prefix', 'backward_flow_'),
                    self.config.get_string("backward_flow_output_key", "backward_flow"),
                    return_data=False
                )
