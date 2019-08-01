import bpy

from src.renderer.Renderer import Renderer
from src.loader.SuncgLoader import SuncgLoader

class SegMapRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config)

    def scaleColor(self, color):
        # 65536 = 2**16 the color depth, 32768 = 2**15 = 2**16/2
        return ((color * 65536) / (bpy.data.scenes["Scene"]["num_labels"])) + ((32768)/(bpy.data.scenes["Scene"]["num_labels"]))
        
    def color_obj(self, obj, color):
        for m in obj.material_slots:
            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links
            emission_node = nodes.new(type='ShaderNodeEmission')
            output = nodes.get("Material Output")

            if color:
                emission_node.inputs[0].default_value[:3] = map(self.scaleColor, color)

            links.new(emission_node.outputs[0], output.inputs[0])

    def run(self):
        self._configure_renderer()

        bpy.context.scene.render.image_settings.color_mode = "BW"
        bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
        bpy.context.scene.render.image_settings.color_depth = "16"

        use_denoising = bpy.context.scene.render.layers[0].cycles.use_denoising
        filter_width = bpy.data.scenes["Scene"].cycles.filter_width

        bpy.context.scene.render.layers[0].cycles.use_denoising = False
        bpy.data.scenes["Scene"].cycles.filter_width = 0.0
        for obj in bpy.context.scene.objects:
            if "modelId" in obj:
                    category_id = obj['category_id']
                    self.color_obj(obj, [category_id, category_id, category_id])

        self._render("seg_")
        self._register_output("seg_", "seg", ".exr")

        bpy.context.scene.render.layers[0].cycles.use_denoising = use_denoising
        bpy.data.scenes["Scene"].cycles.filter_width = filter_width

