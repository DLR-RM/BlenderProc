import bpy

from src.renderer.RendererInterface import RendererInterface
from src.utility.Utility import Utility


class RgbRenderer(RendererInterface):
    """ Renders rgb images for each registered keypoint.

    Images are stored as PNG-files or JPEG-files with 8bit color depth.
    .. csv-table::
        :header: "Parameter", "Description"

        "render_texture_less", "Render all objects with a white slightly glossy texture, does not change emission "
                                "materials, Type: bool. Default: False."
        "image_type", "Image type of saved rendered images, Type: str. Default: 'PNG'. Available: ['PNG','JPEG']"
        "use_motion_blur", "Use Blender motion blur feature which is required for motion blur and rolling shutter simulation. "
                                "This feature only works if camera poses follow a continous trajectory as Blender performs a Bezier "
                                "interpolation between keyframes and therefore arbitrary results are to be expected if camera poses "
                                "are discontinuous (e.g. when sampled), Type: bool. Default: False"
        "motion_blur_length", "Motion blur effect length (in frames), Type: float. Default: 0.1"
        "use_rolling_shutter", "Use rolling shutter simulation (top to bottom). This depends on the setting enable_motion_blur "
        "being activated and a motion_blur_length > 0, Type: bool. Default: False"
        "rolling_shutter_length", "Time as fraction of the motion_blur_length one scanline is exposed when enable_rolling_shutter is "
                                    "activated. If set to 1, this creates a pure motion blur effect, if set to 0 a pure rolling "
                                    "shutter effect, Type: float. Default: 0.2"
    """
    def __init__(self, config):
        RendererInterface.__init__(self, config)
        self._texture_less_mode = config.get_bool('render_texture_less', False)
        self._image_type = config.get_string('image_type', 'PNG')
        self._use_motion_blur = config.get_bool('use_motion_blur', False)
        self._motion_blur_length = config.get_float('motion_blur_length', 0.1)
        self._use_rolling_shutter = config.get_bool('use_rolling_shutter', False)
        self._rolling_shutter_length = config.get_float('rolling_shutter_length', 0.2)

    def change_to_texture_less_render(self):
        """
        Changes the materials, which do not contain a emission shader to a white slightly glossy texture
        :return:
        """
        new_mat = bpy.data.materials.new(name="TextureLess")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes

        principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")

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

    def run(self):
        # if the rendering is not performed -> it is probably the debug case.
        do_undo = not self._avoid_rendering
        with Utility.UndoAfterExecution(perform_undo_op=do_undo):
            self._configure_renderer(use_denoiser=True, default_denoiser="Intel")

            # In case a previous renderer changed these settings
            bpy.context.scene.render.image_settings.color_mode = "RGB"
            bpy.context.scene.render.image_settings.file_format = self._image_type
            bpy.context.scene.render.image_settings.color_depth = "8"

            # only influences jpg quality
            bpy.context.scene.render.image_settings.quality = 95

            # check if texture less render mode is active
            if self._texture_less_mode:
                self.change_to_texture_less_render()

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=True)

            # motion blur
            if self._use_motion_blur:
                bpy.context.scene.render.use_motion_blur = True
                bpy.context.scene.render.motion_blur_shutter = self._motion_blur_length

            # rolling shutter
            if self._use_rolling_shutter:
                bpy.context.scene.cycles.rolling_shutter_type= 'TOP'
                bpy.context.scene.cycles.rolling_shutter_duration = self._rolling_shutter_length

                if not self._use_motion_blur:
                    raise UserWarning("Cannot enable rolling shutter because motion blur is not enabled, "
                                        "see setting use_motion_blur in renderer.RgbRenderer module.")
                if self._motion_blur_length <= 0:
                    raise UserWarning("Cannot enable rolling shutter because no motion blur length is specified, "
                                        "see setting motion_blur_length in renderer.RgbRenderer module.")

            self._render("rgb_")

        if self._image_type == 'PNG':
            self._register_output("rgb_", "colors", ".png", "1.0.0")
        elif self._image_type == 'JPEG':
            self._register_output("rgb_", "colors", ".jpg", "1.0.0")
        else:
            raise Exception("Unknown Image Type " + self._image_type)
