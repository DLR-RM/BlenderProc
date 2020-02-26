import bpy

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility


class RgbRenderer(Renderer):
    """ Renders rgb images for each registered keypoint.

    Images are stored as PNG-files with 8bit color depth.
    .. csv-table::
       :header: "Parameter", "Description"

       "render_texture_less", "Render all objects with a white slightly glossy texture, does not change emission materials, default: False (off)."
       "vertex_colours", "use vertex colours instead of texture, default: False (off)."
    """
    def __init__(self, config):
        Renderer.__init__(self, config)
        self._texture_less_mode = config.get_bool('render_texture_less', False)
        self._vertex_colours = config.get_bool('vertex_colours', False)

    def change_to_texture_less_render(self):
        """
        Changes the materials, which do not contain a emission shader to a white slightly glossy texture
        :return:
        """
        new_mat = bpy.data.materials.new(name="TextureLess")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes

        principled_bsdf = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
        if principled_bsdf and len(principled_bsdf) == 1:
            principled_bsdf = principled_bsdf[0]
        else:
            print("Warning: The generation of the new texture failed, it has more than one Prinicipled BSDF!")

        # setting the color values for the shader
        principled_bsdf.inputs['Specular'].default_value = 0.65  # specular
        principled_bsdf.inputs['Roughness'].default_value = 0.2  # roughness

        for object in [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]:
            # replace all materials with the new texture less material
            for slot in object.material_slots:
                emission_shader = False
                # check if the material contains an emission shader:
                for node in slot.material.node_tree.nodes:
                    # check if one of the shader nodes is a Emission Shader
                    if 'Emission' in node.bl_idname:
                        emission_shader = True
                        break
                # only replace materials, which do not contain any emission shader
                if not emission_shader:
                    if self._use_alpha_channel:
                        slot.material = self.add_alpha_texture_node(slot.material, new_mat)
                    else:
                        slot.material = new_mat

    def change_to_vertex_colours(self):
        new_mat = bpy.data.materials.new(name="VertexColor")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes

        mat_links = new_mat.node_tree.links

        bsdf = nodes.get("Principled BSDF")
        vcol = nodes.new(type="ShaderNodeVertexColor")
        vcol.layer_name = "Col"
        mat_links.new(vcol.outputs['Color'], bsdf.inputs['Base Color'])

        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                ob.active_material = new_mat

    def run(self):
        with Utility.UndoAfterExecution():
            self._configure_renderer(default_denoiser="Intel")

            # In case a previous renderer changed these settings
            bpy.context.scene.render.image_settings.color_mode = "RGB"
            bpy.context.scene.render.image_settings.file_format = "PNG"
            bpy.context.scene.render.image_settings.color_depth = "8"

            # check if texture less render mode is active
            if self._texture_less_mode:
                self.change_to_texture_less_render()

            if self._vertex_colours:
                self.change_to_vertex_colours()

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=True)

            self._render("rgb_")
        self._register_output("rgb_", "colors", ".png", "1.0.0")
