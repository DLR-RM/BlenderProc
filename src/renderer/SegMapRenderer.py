import csv
import os

import bpy
import imageio
import numpy as np

from src.renderer.Renderer import Renderer
from src.utility.ColorPicker import get_colors
from src.utility.Utility import Utility


class SegMapRenderer(Renderer):
    """
    Renders segmentation maps for each registered keypoint.

    The rendering is stored using the .exr file type and a color depth of 16bit to achieve high precision.

    .. csv-table::
       :header: "Parameter", "Description"

       "map_by", "Method to be used for color mapping. Allowed values: instance, class"
    """

    def __init__(self, config):

        Renderer.__init__(self, config)

    def color_obj(self, obj, color):
        """ Adjusts the materials of the given object, s.t. they are ready for rendering the seg map.

        This is done by replacing all nodes just with an emission node, which emits the color corresponding to the category of the object.

        :param obj: The object to use.
        :param color: RGB array of a color.
        """
        # Create new material emitting the given color
        new_mat = bpy.data.materials.new(name="segmentation")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes
        links = new_mat.node_tree.links
        emission_node = nodes.new(type='ShaderNodeEmission')
        output = nodes.get("Material Output")

        emission_node.inputs[0].default_value[:3] = [c / 255 for c in color]
        links.new(emission_node.outputs[0], output.inputs[0])

        # Set material to be used for coloring all faces of the given object
        for i in range(len(obj.material_slots)):
            obj.data.materials[i] = new_mat

    def run(self):
        with Utility.UndoAfterExecution():
            self._configure_renderer(default_samples=1)

            # get current method for color mapping, instance or class
            method = self.config.get_string("map_by", "class")

            if method == "class":
                # Generated colors for each class
                rgbs = get_colors(bpy.data.scenes["Scene"]["num_labels"])
                class_to_rgb = {}
                cur_idx = 0
            else:
                # Generated colors for each instance
                rgbs = get_colors(len(bpy.context.scene.objects))

            hexes = [Utility.rgb_to_hex(rgb) for rgb in rgbs]

            # Initialize maps
            color_map = []

            bpy.context.scene.render.image_settings.color_mode = "BW"
            bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
            bpy.context.scene.render.image_settings.color_depth = "16"
            bpy.context.view_layer.cycles.use_denoising = False
            bpy.data.scenes["Scene"].cycles.filter_width = 0.0

            for idx, obj in enumerate(bpy.context.scene.objects):

                # if class specified for this object or not
                if "category_id" in obj:
                    _class = obj['category_id']
                else:
                    _class = None

                # if method to assign color is by class or by instance
                if method == "class" and _class is not None:
                    if _class not in class_to_rgb:  # if class has not been assigned a color yet
                        class_to_rgb[_class] = {
                            "rgb": rgbs[cur_idx],
                            "rgb_idx": cur_idx,
                            "_hex": Utility.rgb_to_hex(rgbs[cur_idx])
                        }  # assign the class with a color
                        cur_idx += 1  # set counter to next avialable color
                    rgb = class_to_rgb[_class]["rgb"]  # assign this object the color of this class
                    color_idx = class_to_rgb[_class]["rgb_idx"]  # get idx of assigned color
                else:
                    rgb = rgbs[idx]  # assign this object a color
                    color_idx = idx  # each instance to color is one to one mapping, both have same idx

                # add values to a map
                color_map.append({'color': rgb, 'objname': obj.name, 'class': _class, 'idx': color_idx})

                self.color_obj(obj, rgb)

            self._render("seg_")

            # After rendering
            for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):  # for each rendered frame
                file_path = os.path.join(self._determine_output_dir(), "seg_" + "%04d" % frame + ".exr")
                segmentation = imageio.imread(file_path)[:, :, :3]
                segmentation = np.round(segmentation * 255).astype(int)

                segmap = np.zeros(segmentation.shape[:2])  # initialize mask

                for idx, row in enumerate(segmentation):
                    segmap[idx, :] = [Utility.get_idx(hexes, Utility.rgb_to_hex(rgb)) for rgb in row]
                fname = os.path.join(self._determine_output_dir(), "segmap_" + "%04d" % frame)
                np.save(fname, segmap)

            # write color mappings to file
            with open(os.path.join(self._determine_output_dir(), "class_inst_col_map.csv"), 'w', newline='') as csvfile:
                fieldnames = list(color_map[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for mapping in color_map:
                    writer.writerow(mapping)

        self._register_output("segmap_", "segmap", ".npy", "1.0.0")
        self._register_output("class_inst_col_map", "segcolormap", ".csv", "1.0.0", unique_for_camposes=False)
