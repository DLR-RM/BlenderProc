import bpy
import os
from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility
from src.utility.ColorPicker import get_colors, rgb_to_hex
from random import uniform


class SegMapRenderer(Renderer):

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
        :param color: RGB array of a color.
        """
        for m in obj.material_slots:
            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links
            emission_node = nodes.new(type='ShaderNodeEmission')
            output = nodes.get("Material Output")

            emission_node.inputs[0].default_value[:3] = [c/255 for c in color]
            links.new(emission_node.outputs[0], output.inputs[0])

    def run(self):
        """ Renders segmentation maps for each registered keypoint.

        The rendering is stored using the .exr filetype and a color depth of 16bit to achieve high precision.
        """
        with Utility.UndoAfterExecution():
            self._configure_renderer()
            
            # get current method for color mapping, instance or class
            method = self.config.get_string("map_by", "class") 
            
            # Generate color palette where visual color distance is maximized 
            colors = get_colors(len(bpy.context.scene.objects))
            color_mapping = []
            bpy.context.scene.render.image_settings.color_mode = "BW"
            bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
            bpy.context.scene.render.image_settings.color_depth = "16"

            bpy.context.view_layer.cycles.use_denoising = False
            bpy.data.scenes["Scene"].cycles.filter_width = 0.0
            for idx, obj in enumerate(bpy.context.scene.objects):
                # find color according to method given in config
                color = [0,0,0] # initialize color
                if method == "class": # if the map_by is not specifically set to "instance" then map color by class
                    # this scheme specifically works for suncg dataset only
                    if "modelId" in obj:
                        category_id = obj['category_id']
                        color = [category_id, category_id, category_id] # Assign class label to each channel
                        color = map(self.scale_color, color) # Now scale each color from [0-C] to [0 - 255] while keeping uniform distance between two classes
                else:
                    color = colors[idx]
                color_mapping.append([obj.name,rgb_to_hex(color)])
                if 'category_id' in obj:
                    color_mapping[idx].append(obj['category_id'])
                self.color_obj(obj, color)
            
            outpath = os.path.join(self.output_dir, "segment_colo_map")
            with open(outpath, 'w') as f:
               for mapping in color_mapping:
                    f.write(','.join(mapping)+'\n')
                    
            self._render("seg_")

        self._register_output("seg_", "seg", ".exr", "2.0.1")
