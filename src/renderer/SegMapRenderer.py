import bpy

from src.renderer.Renderer import Renderer
from src.loader.SuncgLoader import SuncgLoader

class SegMapRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config, undo_after_run=True)


    def _get_spaced_colors(self, n):
        max_value = 16581375 #255**3
        interval = int(max_value / n)
        colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]
        return [((float(int(i[:2], 16)/255.0)), (float(int(i[2:4], 16)/255.0)), (float(int(i[4:], 16))/255.0)) for i in colors]

    
    # Just for debugging the colors in the 0->255 range
    def __get_spaced_colors(self, n):
        max_value = 16581375 #255**3
        interval = int(max_value / n)
        colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]
        return [(float(int(i[:2], 16)), float(int(i[2:4], 16)), float(int(i[4:], 16))) for i in colors]

    def s2lin(self, x):
        a = 0.055
        if x <= 0.0404482362771082:
            y = x * (1.0 / 12.92)
        else:
            y = pow( (x + a) * (1.0 / (1 + a)), 2.4)
        return y


    def lin2srgb(self, lin):
        if lin > 0.0031308:
            s = 1.055 * (pow(lin, (1.0 / 2.4))) - 0.055
        else:
            s = 12.92 * lin
        return s


    def scaleColor(self, color):
        return ((float(color)/float(SuncgLoader.num_labels)) * 2**16) + float(2**15)/float(SuncgLoader.num_labels)
        
    def color_obj(self, obj, color=None):
        for m in obj.material_slots:
            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links
            emission_node = nodes.new(type='ShaderNodeEmission')
            output = nodes.get("Material Output")

            if color:
                emission_node.inputs[0].default_value[:3] = map(self.scaleColor, color)
            else:
                emission_node.inputs[0].default_value[:3] = (0.0, 0.0, 0.0)
            links.new(emission_node.outputs[0], output.inputs[0])



    def run(self):
        self._configure_renderer()

        bpy.context.scene.render.image_settings.color_mode = "BW"
        bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
        bpy.context.scene.render.image_settings.color_depth = "16"
        bpy.context.scene.render.layers[0].cycles.use_denoising = False
        bpy.data.scenes["Scene"].cycles.filter_width = 0.0
        fdg = set()
        for obj in bpy.context.scene.objects:
            if "modelId" in obj:
                obj_id = obj["modelId"]
                if obj["type"] != "Room":
                    category_id = obj['category_id']
                    fdg.add(category_id)
                    # self.color_obj(obj, [category_id/255.0, category_id/255.0, category_id/255.0])
                    self.color_obj(obj, [category_id, category_id, category_id])

                else:
                    self.color_obj(obj)

        print(fdg)
        print(SuncgLoader.num_labels)
        self._render("seg_")
