import csv
import os

import bpy
import imageio
import numpy as np

from src.renderer.Renderer import Renderer
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

    def _colorize_object(self, obj, color):
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
        if len(obj.material_slots) > 0:
            for i in range(len(obj.material_slots)):
                obj.data.materials[i] = new_mat
        else:
            obj.data.materials.append(new_mat)

    def _set_world_background_color(self, color):
        """ Set the background color of the blender world obejct.

        :param color: A 3-dim array containing the background color in range [0, 255]
        """
        nodes = bpy.context.scene.world.node_tree.nodes
        nodes.get("Background").inputs[0].default_value = [c / 255 for c in color] + [1]

    def _colorize_objects_for_semantic_segmentation(self, objects):
        """ Sets the color of each object according to their category_id.

        :param objects: A list of objects.
        :return: The num_splits_per_dimension of the spanned color space, the color map
        """
        colors, num_splits_per_dimension = Utility.span_equally_spaced_color_space(bpy.context.scene["num_labels"] + 1)

        for obj in objects:
            if "category_id" not in obj:
                raise Exception("The object " + obj.name + " does not have a category_id.")

            self._colorize_object(obj, colors[obj["category_id"]])

        # Set world background label
        if "category_id" not in bpy.context.scene.world:
            raise Exception("The world does not have a category_id. It will be used to set the label of the world background.")
        self._set_world_background_color(colors[bpy.context.scene.world["category_id"]])

        return colors, num_splits_per_dimension, None

    def _colorize_objects_for_instance_segmentation(self, objects):
        """ Sets a different color to each object.

        :param objects: A list of objects.
        :return: The num_splits_per_dimension of the spanned color space, the color map
        """
        colors, num_splits_per_dimension = Utility.span_equally_spaced_color_space(len(objects) + 1)

        color_map = []
        for idx, obj in enumerate(objects):
            self._colorize_object(obj, colors[idx])

            obj_class = obj["category_id"] if "category_id" in obj else None
            color_map.append({'objname': obj.name, 'class': obj_class, 'idx': idx})

        # Set world background label
        self._set_world_background_color(colors[-1])
        color_map.append({'objname': "background", 'class': -1, 'idx': len(colors) - 1})

        return colors, num_splits_per_dimension, color_map

    def run(self):
        with Utility.UndoAfterExecution():
            self._configure_renderer(default_samples=1)

            # get current method for color mapping, instance or class
            method = self.config.get_string("map_by", "class")

            # Get objects with materials (i.e. not lights or cameras)
            objs_with_mats = [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]

            if method == "class":
                colors, num_splits_per_dimension, color_map = self._colorize_objects_for_semantic_segmentation(objs_with_mats)
            elif method == "instance":
                colors, num_splits_per_dimension, color_map = self._colorize_objects_for_instance_segmentation(objs_with_mats)
            else:
                raise Exception("Invalid mapping method: " + method)

            bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
            bpy.context.scene.render.image_settings.color_depth = "16"
            bpy.context.view_layer.cycles.use_denoising = False
            bpy.context.scene.cycles.filter_width = 0.0

            self._render("seg_")

            # Find optimal dtype of output based on max index
            for dtype in [np.uint8, np.uint16, np.uint32]:
                optimal_dtype = dtype
                if np.iinfo(optimal_dtype).max >= len(colors) - 1:
                    break

            # After rendering
            for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):  # for each rendered frame
                file_path = os.path.join(self._determine_output_dir(), "seg_" + "%04d" % frame + ".exr")
                segmentation = imageio.imread(file_path)[:, :, :3]
                segmentation = np.round(segmentation * 255).astype(optimal_dtype)

                segmap = Utility.map_back_from_equally_spaced_color_space(segmentation, num_splits_per_dimension)

                fname = os.path.join(self._determine_output_dir(), "segmap_" + "%04d" % frame)
                np.save(fname, segmap)

            # write color mappings to file
            if color_map is not None:
                with open(os.path.join(self._determine_output_dir(), "class_inst_col_map.csv"), 'w', newline='') as csvfile:
                    fieldnames = list(color_map[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for mapping in color_map:
                        writer.writerow(mapping)

        self._register_output("segmap_", "segmap", ".npy", "1.0.0")
        if color_map is not None:
            self._register_output("class_inst_col_map", "segcolormap", ".csv", "1.0.0", unique_for_camposes=False)
