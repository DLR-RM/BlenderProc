import bpy

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility


class RgbRenderer(Renderer):
    """ Renders rgb images for each registered keypoint.

    Images are stored as PNG-files with 8bit color depth.
    .. csv-table::
       :header: "Parameter", "Description"

       "render_texture_less", "Render all objects with a white slightly glossy texture, does not change emission materials, default: False (off)."
    """
    def __init__(self, config):
        Renderer.__init__(self, config)
        self._texture_less_mode = config.get_bool('render_texture_less')

    def change_to_texture_less_render(self):
        """
        Changes the materials, which do not contain a emission shader to a white slightly glossy texture
        :return:
        """
        new_mat = bpy.data.materials.new(name="TextureLess")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes
        principled_bsdf = nodes.get("Principled BSDF")

        # setting the color values for the shader
        principled_bsdf.inputs[5].default_value = 0.65 # specular
        principled_bsdf.inputs[7].default_value = 0.2  # roughness

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

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=True)

            self._render("rgb_")
        self._register_output("rgb_", "colors", ".png", "1.0.0")
