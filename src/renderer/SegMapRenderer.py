import bpy

from src.renderer.Renderer import Renderer
from src.materials.SuncgMaterials import SuncgMaterials

class SegMapRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config)


    def _get_spaced_colors(self, n):
        max_value = 16581375 #255**3
        interval = int(max_value / n)
        colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]
        return [(float(int(i[:2], 16)/255.0), float(int(i[2:4], 16)/255.0), float(int(i[4:], 16))/255.0) for i in colors]
    def run(self):
        self._configure_renderer()
        self.color_palette = self._get_spaced_colors(len(SuncgMaterials.get_labels()))

        for obj in bpy.context.scene.objects:
            if "modelId" in obj:
                obj_id = obj["modelId"]
                if obj["type"] != "Room":
                    category_id = SuncgMaterials._get_label_id(obj_id)

                    for m in obj.material_slots:
                        nodes = m.material.node_tree.nodes
                        links = m.material.node_tree.links

                        emission_node = nodes.new(type='ShaderNodeEmission')
                        output = nodes.get("Material Output")
                        emission_node.inputs[0].default_value[:3] = self.color_palette[category_id]
                    
                        links.new(emission_node.outputs[0], output.inputs[0])

        self._render("seg_")
