import bpy

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility

class NormalRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config)

    def _create_normal_material(self):
        """ Creates a new material which uses xyz normal coordinates as rgb.

        This assumes a linear color space used for rendering!
        """
        new_mat = bpy.data.materials.new(name="Normal")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes
        nodes.remove(nodes.get("Principled BSDF"))

        links = new_mat.node_tree.links
        texture_coord_node = nodes.new(type='ShaderNodeTexCoord')
        vector_transform_node = nodes.new(type='ShaderNodeVectorTransform')
        vector_transform_node.vector_type = "NORMAL"
        vector_transform_node.convert_from = "OBJECT"
        vector_transform_node.convert_to = "CAMERA"

        mapping_node = nodes.new(type='ShaderNodeMapping')
        mapping_node.vector_type = "TEXTURE"
        mapping_node.translation = [-1, -1, 1]
        mapping_node.scale = [2, 2, -2]

        emission_node = nodes.new(type='ShaderNodeEmission')

        output_node = nodes.get("Material Output")

        links.new(texture_coord_node.outputs[1], vector_transform_node.inputs[0])
        links.new(vector_transform_node.outputs[0], mapping_node.inputs[0])
        links.new(mapping_node.outputs[0], emission_node.inputs[0])
        links.new(emission_node.outputs[0], output_node.inputs[0])
        return new_mat

    def run(self):
        """ Renders normal images for each registered keypoint.

        Every object's materials are replaced with an imported normal material to render normals.
        The rendering is stored using the .exr filetype and a color depth of 32bit to achieve high precision.
        """
        with Utility.UndoAfterExecution():
            self._configure_renderer()

            new_mat = self._create_normal_material()

            # render normals
            bpy.context.scene.cycles.samples = self.config.get_int("samples", 100)  # to smooth the result
            bpy.context.view_layer.cycles.use_denoising = False
            for obj in bpy.context.scene.objects:
                if len(obj.material_slots) > 0:
                    for i in range(len(obj.material_slots)):
                        obj.data.materials[i] = new_mat
                elif hasattr(obj.data, 'materials'):
                    obj.data.materials.append(new_mat)

            # Set the color channel depth of the output to 32bit
            bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
            bpy.context.scene.render.image_settings.color_depth = "32"

            self._render("normal_")

        self._register_output("normal_", "normal", ".exr", "2.0.0")