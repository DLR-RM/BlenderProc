import bpy
import os
import numpy as np

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility
from src.utility.BlenderUtility import load_flow


class FlowRenderer(Renderer):
    """ Renders optical flow between consecutive keypoints.

    .. csv-table::
        :header: "Parameter", "Description"

    """

    def __init__(self, config):
        Renderer.__init__(self, config)

    def _output_vector_field(self):
        """ Configures compositor to output speed vectors. """

        # Flow settings (is called "vector" in blender)
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        bpy.context.scene.view_layers["View Layer"].use_pass_vector = True

        # Adapt compositor to output vector field
        tree = bpy.context.scene.node_tree
        links = tree.links

        # Use existing render layer
        render_layer_node = tree.nodes.get('Render Layers')

        # Create output file
        output_file = tree.nodes.new('CompositorNodeOutputFile')
        output_file.base_path = self._determine_output_dir()
        output_file.format.file_format = "OPEN_EXR"
        output_file.file_slots.values()[0].path = self.config.get_string("flow_output_file_prefix", "flow_")
        # Link render layer to output file
        links.new(render_layer_node.outputs['Vector'], output_file.inputs['Image'])

    def run(self):
        # determine whether to get optical flow or scene flow - get scene flow per default
        get_forward_flow = self.config.get_bool('forward_flow', False)
        get_backward_flow = (self.config.get_bool('backward_flow', False) if get_forward_flow is True else True)

        with Utility.UndoAfterExecution():
            self._configure_renderer()

            self._output_vector_field()

            # Determine pathes to convert the vector field after rendering
            temporary_vector_file_path = os.path.join(self._temp_dir, 'flow_')
            self._render("flow_", custom_file_path=temporary_vector_file_path)

            # After rendering: convert to optical flow or calculate hsv visualization, if desired
            for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
                file_path = temporary_vector_file_path + "%04d" % frame + ".exr"
                vector_field = load_flow(file_path).astype(np.float32)

                # temporarily save respective vector fields
                if get_forward_flow:
                    fname = os.path.join(self._determine_output_dir(),
                                         self.config.get_string('forward_flow_output_file_prefix',
                                                                'forward_flow_')) + '%04d' % frame
                    np.save(fname + '.npy', vector_field[:, :, 2:])
                if get_backward_flow:
                    fname = os.path.join(self._determine_output_dir(),
                                         self.config.get_string('backward_flow_output_file_prefix', 'backward_flow_')) + '%04d' % frame
                    np.save(fname + '.npy', vector_field[:, :, :2])

        # register desired outputs  # TODO: hardcoded unique_for_camposes
        use_stereo = self.config.get_bool("stereo", False)
        unique_for_camposes = True

        if get_forward_flow:
            self._add_output_entry({
                "key": self.config.get_string("forward_flow_output_key", "forward_flow"),
                "path": os.path.join(self._determine_output_dir(),
                                     self.config.get_string('forward_flow_output_file_prefix', 'forward_flow_')) + (
                            "%04d" if unique_for_camposes else "") + '.npy',
                "version": '2.0.0',
                "stereo": use_stereo
            })

        if get_backward_flow:
            self._add_output_entry({
                "key": self.config.get_string("backward_flow_output_key", "backward_flow"),
                "path": os.path.join(self._determine_output_dir(),
                                     self.config.get_string('backward_flow_output_file_prefix', 'backward_flow_')) + (
                            "%04d" if unique_for_camposes else "") + '.npy',
                "version": '2.0.0',
                "stereo": use_stereo
            })
