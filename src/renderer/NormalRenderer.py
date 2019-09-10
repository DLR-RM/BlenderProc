import bpy

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility

class NormalRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config)

    def run(self):
        """ Renders normal images for each registered keypoint.

        Every object's materials are replaced with an imported normal material to render normals.
        The rendering is stored using the .exr filetype and a color depth of 32bit to achieve high precision.
        """
        with Utility.UndoAfterExecution():
            self._configure_renderer()

            # read normal material
            normal_material_file = self.config.get_string("normal_material_path", "Normal_Material.blend")
            with bpy.data.libraries.load(normal_material_file) as (data_from, data_to):
                data_to.materials = data_from.materials

            # render normals
            bpy.context.scene.cycles.samples = self.config.get_int("samples", 100)  # to smooth the result
            bpy.context.view_layer.cycles.use_denoising = False
            new_mat = bpy.data.materials["Normal"]
            for obj in bpy.context.scene.objects:
                if len(obj.material_slots) > 0:
                    for i in range(len(obj.material_slots)):
                        obj.data.materials[i] = new_mat

            # Set the color channel depth of the output to 32bit
            bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
            bpy.context.scene.render.image_settings.color_depth = "32"

            self._render("normal_")

        self._register_output("normal_", "normal", ".exr", "2.0.0")