import os

import bpy
import numpy as np

from src.renderer.RendererInterface import RendererInterface
from src.utility.BlenderUtility import load_image
from src.utility.RendererUtility import RendererUtility
from src.utility.Utility import Utility


class FlowRendererUtility:

    @staticmethod
    def _output_vector_field(forward_flow, backward_flow, output_dir):
        """ Configures compositor to output speed vectors.

        :param forward_flow: Whether to render forward optical flow.
        :param backward_flow: Whether to render backward optical flow.
        :param output_dir: The directory to write images to.
        """

        # Flow settings (is called "vector" in blender)
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        bpy.context.scene.view_layers["View Layer"].use_pass_vector = True

        # Adapt compositor to output vector field
        tree = bpy.context.scene.node_tree
        links = tree.links

        # Use existing render layer
        render_layer_node = tree.nodes.get('Render Layers')

        separate_rgba = tree.nodes.new('CompositorNodeSepRGBA')
        links.new(render_layer_node.outputs['Vector'], separate_rgba.inputs['Image'])

        if forward_flow:
            combine_fwd_flow = tree.nodes.new('CompositorNodeCombRGBA')
            links.new(separate_rgba.outputs['B'], combine_fwd_flow.inputs['R'])
            links.new(separate_rgba.outputs['A'], combine_fwd_flow.inputs['G'])
            fwd_flow_output_file = tree.nodes.new('CompositorNodeOutputFile')
            fwd_flow_output_file.base_path = output_dir
            fwd_flow_output_file.format.file_format = "OPEN_EXR"
            fwd_flow_output_file.file_slots.values()[0].path = "fwd_flow_"
            links.new(combine_fwd_flow.outputs['Image'], fwd_flow_output_file.inputs['Image'])

        if backward_flow:
            # actually need to split - otherwise the A channel of the image is getting weird, no idea why
            combine_bwd_flow = tree.nodes.new('CompositorNodeCombRGBA')
            links.new(separate_rgba.outputs['R'], combine_bwd_flow.inputs['R'])
            links.new(separate_rgba.outputs['G'], combine_bwd_flow.inputs['G'])
            bwd_flow_output_file = tree.nodes.new('CompositorNodeOutputFile')
            bwd_flow_output_file.base_path = output_dir
            bwd_flow_output_file.format.file_format = "OPEN_EXR"
            bwd_flow_output_file.file_slots.values()[0].path = "bwd_flow_"
            links.new(combine_bwd_flow.outputs['Image'], bwd_flow_output_file.inputs['Image'])

    @staticmethod
    def render(output_dir, temp_dir, get_forward_flow, get_backward_flow, blender_image_coordinate_style=False, forward_flow_output_file_prefix="forward_flow_", forward_flow_output_key="forward_flow", backward_flow_output_file_prefix="backward_flow_", backward_flow_output_key="backward_flow"):
        """ Renders the optical flow (forward and backward) for all frames.

        :param output_dir: The directory to write images to.
        :param temp_dir: The directory to write intermediate data to.
        :param get_forward_flow: Whether to render forward optical flow.
        :param get_backward_flow: Whether to render backward optical flow.
        :param blender_image_coordinate_style: Whether to specify the image coordinate system at the bottom left (blender default; True) or top left (standard convention; False).
        :param forward_flow_output_file_prefix: The file prefix that should be used when writing forward flow to a file.
        :param forward_flow_output_key: The key which should be used for storing forward optical flow values.
        :param backward_flow_output_file_prefix: The file prefix that should be used when writing backward flow to a file.
        :param backward_flow_output_key: The key which should be used for storing backward optical flow values.
        """
        if get_forward_flow is False and get_backward_flow is False:
            raise Exception("Take the FlowRenderer Module out of the config if both forward and backward flow are set to False!")

        with Utility.UndoAfterExecution():
            RendererUtility.init()
            RendererUtility.set_samples(1)
            RendererUtility.set_adaptive_sampling(0)
            RendererUtility.set_denoiser(None)
            RendererUtility.set_light_bounces(1, 0, 0, 1, 0, 8, 0)

            FlowRendererUtility._output_vector_field(get_forward_flow, get_backward_flow, output_dir)

            # only need to render once; both fwd and bwd flow will be saved
            temporary_fwd_flow_file_path = os.path.join(temp_dir, 'fwd_flow_')
            temporary_bwd_flow_file_path = os.path.join(temp_dir, 'bwd_flow_')
            RendererUtility.render(temp_dir, "bwd_flow_", None)

            # After rendering: convert to optical flow or calculate hsv visualization, if desired
            for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
                # temporarily save respective vector fields
                if get_forward_flow:
                    file_path = temporary_fwd_flow_file_path + "%04d" % frame + ".exr"
                    fwd_flow_field = load_image(file_path, num_channels=4).astype(np.float32)

                    if not blender_image_coordinate_style:
                        fwd_flow_field[:, :, 1] = fwd_flow_field[:, :, 1] * -1

                    fname = os.path.join(output_dir, forward_flow_output_file_prefix) + '%04d' % frame
                    forward_flow = fwd_flow_field * -1  # invert forward flow to point at next frame
                    np.save(fname + '.npy', forward_flow[:, :, :2])

                if get_backward_flow:
                    file_path = temporary_bwd_flow_file_path + "%04d" % frame + ".exr"
                    bwd_flow_field = load_image(file_path, num_channels=4).astype(np.float32)

                    if not blender_image_coordinate_style:
                        bwd_flow_field[:, :, 1] = bwd_flow_field[:, :, 1] * -1

                    fname = os.path.join(output_dir, backward_flow_output_file_prefix) + '%04d' % frame
                    np.save(fname + '.npy', bwd_flow_field[:, :, :2])

        # register desired outputs
        if get_forward_flow:
            Utility.register_output(output_dir, forward_flow_output_file_prefix, forward_flow_output_key, '.npy', '2.0.0')
        if get_backward_flow:
            Utility.register_output(output_dir, backward_flow_output_file_prefix, backward_flow_output_key, '.npy', '2.0.0')
