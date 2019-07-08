import bpy

from src.renderer.Renderer import Renderer


class NormalRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config)

    def run(self):
        self._configure_renderer()

        # read normal material
        normal_material_file = self.config.get_string("normal_material_path", "Normal_Material.blend")
        with bpy.data.libraries.load(normal_material_file) as (data_from, data_to):
            data_to.materials = data_from.materials

        # render normals
        self.scene.cycles.samples = 100  # to smooth the result
        self.scene.render.layers[0].cycles.use_denoising = False
        new_mat = bpy.data.materials["Normal"]
        for obj in bpy.context.scene.objects:
            if len(obj.material_slots) > 0:
                for i in range(len(obj.material_slots)):
                    obj.data.materials[i] = new_mat

        self._render("normal_")
