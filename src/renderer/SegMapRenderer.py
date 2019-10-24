import bpy

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility


class SegMapRenderer(Renderer):
    """ Renders segmentation maps for each registered keypoint.

    The rendering is stored using the .exr filetype and a color depth of 16bit to achieve high precision.
    """

    def __init__(self, config):
        Renderer.__init__(self, config)

    def scale_color(self, color):
        """ Maps color values to the range [0, 2^16], s.t. the space between the mapped colors is maximized.

        :param color: An integer representing the index of the color has to be in [0, "num_labels" - 1]
        :return: The integer representing the final color.
        """
        # 65536 = 2**16 the color depth, 32768 = 2**15 = 2**16/2
        return ((color * 65536) / (bpy.data.scenes["Scene"]["num_labels"])) + (32768 / (bpy.data.scenes["Scene"]["num_labels"]))

    def color_obj(self, obj, color):
        """ Adjusts the materials of the given object, s.t. they are ready for rendering the seg map.

        This is done by replacing all nodes just with an emission node, which emits the color corresponding to the category of the object.

        :param obj: The object to use.
        :param color: The color index of the object.
        """
        for m in obj.material_slots:
            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links
            emission_node = nodes.new(type='ShaderNodeEmission')
            output = nodes.get("Material Output")

            emission_node.inputs[0].default_value[:3] = map(self.scale_color, color)

            links.new(emission_node.outputs[0], output.inputs[0])

    def run(self):
        with Utility.UndoAfterExecution():
            self._configure_renderer()

            bpy.context.scene.render.image_settings.color_mode = "BW"
            bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
            bpy.context.scene.render.image_settings.color_depth = "16"

            bpy.context.scene.cycles.samples = 1 # this gives the best result for emission shader
            bpy.context.view_layer.cycles.use_denoising = False
            bpy.data.scenes["Scene"].cycles.filter_width = 0.0
            for obj in bpy.context.scene.objects:
                if "modelId" in obj:
                    category_id = obj['category_id']
                    self.color_obj(obj, [category_id, category_id, category_id])

            self._render("seg_")

        self._register_output("seg_", "seg", ".exr", "2.0.1")
