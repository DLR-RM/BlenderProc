import csv
import os

import bpy
import numpy as np

from src.renderer.RendererInterface import RendererInterface
from src.utility.BlenderUtility import load_image, get_all_mesh_objects
from src.utility.Utility import Utility


class SegMapRenderer(RendererInterface):
    """
    Renders segmentation maps for each registered keypoint.

    The rendering is stored using the .exr file type and a color depth of 16bit to achieve high precision.

    .. csv-table::
       :header: "Parameter", "Description"

       "map_by", "Method to be used for color mapping. Type: string. Default: "class" Available: [instance, class]"
       "segcolormap_output_key", "The key which should be used for storing the class instance to color mapping in"
                                 "a merged file. Type: string. Default: "segcolormap""
       "segcolormap_output_file_prefix", "The file prefix that should be used when writing the class instance to"
                                         "color mapping to file. Type: string. Default: class_inst_col_map"
       "output_file_prefix", "The file prefix that should be used when writing semantic information to a file."
                             "Type: string, Default: "segmap_""
    """

    def __init__(self, config):
        RendererInterface.__init__(self, config)
        # As we use float16 for storing the rendering, the interval of integers which can be precisely
        # stored is [-2048, 2048]. As blender does not allow negative values for colors, we use [0, 2048] ** 3 as our
        # color space which allows ~8 billion different colors/objects. This should be enough.
        self.render_colorspace_size_per_dimension = 2048

    def _colorize_object(self, obj, color):
        """ Adjusts the materials of the given object, s.t. they are ready for rendering the seg map.

        This is done by replacing all nodes just with an emission node, which emits the color corresponding to the
        category of the object.

        :param obj: The object to use.
        :param color: RGB array of a color in the range of [0, self.render_colorspace_size_per_dimension].
        """
        # Create new material emitting the given color
        new_mat = bpy.data.materials.new(name="segmentation")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes
        links = new_mat.node_tree.links
        emission_node = nodes.new(type='ShaderNodeEmission')
        output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')

        emission_node.inputs['Color'].default_value[:3] = color
        links.new(emission_node.outputs['Emission'], output.inputs['Surface'])

        # Set material to be used for coloring all faces of the given object
        if len(obj.material_slots) > 0:
            for i in range(len(obj.material_slots)):
                if self._use_alpha_channel:
                    obj.data.materials[i] = self.add_alpha_texture_node(obj.material_slots[i].material, new_mat)
                else:
                    obj.data.materials[i] = new_mat
        else:
            obj.data.materials.append(new_mat)

    def _set_world_background_color(self, color):
        """ Set the background color of the blender world obejct.

        :param color: A 3-dim array containing the background color in range [0, 255]
        """
        nodes = bpy.context.scene.world.node_tree.nodes
        nodes.get("Background").inputs['Color'].default_value = color + [1]

    def _colorize_objects_for_instance_segmentation(self, objects):
        """ Sets a different color to each object.

        :param objects: A list of objects.
        :return: The num_splits_per_dimension of the spanned color space, the color map
        """
        # + 1 for the background
        colors, num_splits_per_dimension = Utility.generate_equidistant_values(len(objects) + 1,
                                                                               self.render_colorspace_size_per_dimension)
        # this list maps ids in the image back to the objects
        color_map = []

        # Set world background label, which is always label zero
        self._set_world_background_color(colors[0])
        color_map.append(bpy.context.scene.world)  # add the world background as an object to this list

        for idx, obj in enumerate(objects):
            self._colorize_object(obj, colors[idx + 1])
            color_map.append(obj)

        return colors, num_splits_per_dimension, color_map

    def run(self):
        with Utility.UndoAfterExecution():
            self._configure_renderer(default_samples=1)


            # Get objects with meshes (i.e. not lights or cameras)
            objs_with_mats = get_all_mesh_objects()

            colors, num_splits_per_dimension, used_objects = self._colorize_objects_for_instance_segmentation(
                objs_with_mats)

            bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
            bpy.context.scene.render.image_settings.color_depth = "16"
            bpy.context.view_layer.cycles.use_denoising = False
            bpy.context.scene.cycles.filter_width = 0.0

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=False)

            # Determine path for temporary and for final output
            temporary_segmentation_file_path = os.path.join(self._temp_dir, "seg_")
            final_segmentation_file_path = os.path.join(self._determine_output_dir(),
                                                        self.config.get_string("output_file_prefix", "segmap_"))

            # Render the temporary output
            self._render("seg_", custom_file_path=temporary_segmentation_file_path)

            # get current method for color mapping, instance or class
            method = self.config.get_string("map_by", "class")

            # Find optimal dtype of output based on max index
            for dtype in [np.uint8, np.uint16, np.uint32]:
                optimal_dtype = dtype
                if np.iinfo(optimal_dtype).max >= len(colors) - 1:
                    break


            used_attribute = self.config.get_raw_dict("map_by", "instance")

            if isinstance(used_attribute, str):
                # only one result is requested
                result_channels = 1
                used_attribute = [used_attribute]
            elif isinstance(used_attribute, list):
                result_channels = len(used_attribute)
            else:
                raise Exception("The type of this is not supported here: {}".format(used_attribute))

            save_in_csv_attributes = {}

            # After rendering
            if not self._avoid_rendering:
                for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):  # for each rendered frame
                    file_path = temporary_segmentation_file_path + "%04d" % frame + ".exr"
                    segmentation = load_image(file_path)

                    segmap = Utility.map_back_from_equally_spaced_equidistant_values(segmentation,
                                                                                     num_splits_per_dimension,
                                                                                     self.render_colorspace_size_per_dimension)
                    segmap = segmap.astype(optimal_dtype)

                    used_object_ids = np.unique(segmap)
                    combined_result_map = []
                    for channel_id in range(result_channels):
                        resulting_map = np.empty((segmap.shape[0], segmap.shape[1]))
                        was_used = False
                        current_attribute = used_attribute[channel_id]
                        # if the class is used the category_id attribute is evaluated
                        if current_attribute == "class":
                            current_attribute = "cp_category_id"
                        # in the instance case the resulting ids are directly used
                        if current_attribute == "instance":
                            resulting_map = segmap
                            was_used = True
                        else:
                            for object_id in used_object_ids:
                                current_obj = used_objects[object_id]
                                if hasattr(current_obj, current_attribute):
                                    used_value = getattr(current_obj, current_attribute)
                                    try:
                                        resulting_map[segmap == object_id] = used_value
                                        was_used = True
                                    except ValueError:
                                        if object_id in save_in_csv_attributes:
                                            save_in_csv_attributes[object_id][current_attribute] = used_value
                                        else:
                                            save_in_csv_attributes[object_id] = {current_attribute: used_value}
                                elif current_attribute.startswith("cp_") and current_attribute[len("cp_"):] in current_obj:
                                    used_value = current_obj[current_attribute[len("cp_"):]]
                                    try:
                                        resulting_map[segmap == object_id] = used_value
                                        was_used = True
                                    except ValueError:
                                        if object_id in save_in_csv_attributes:
                                            save_in_csv_attributes[object_id][current_attribute] = used_value
                                        else:
                                            save_in_csv_attributes[object_id] = {current_attribute: used_value}
                                else:
                                    raise Exception("The obj: {} does not have the "
                                                    "attribute: {}".format(current_obj.name, current_attribute))
                        if was_used:
                            combined_result_map.append(resulting_map)

                    fname = final_segmentation_file_path + "%04d" % frame
                    resulting_map = np.stack(combined_result_map, axis=2)
                    np.save(fname, resulting_map)

            # write color mappings to file
            if objs_with_mats and not self._avoid_rendering:
                csv_file_path = os.path.join(self._determine_output_dir(),
                                             self.config.get_string("segcolormap_output_file_prefix",
                                                                    "class_inst_col_map") + ".csv")
                with open(csv_file_path, 'w', newline='') as csvfile:
                    # get from the first element the used field names
                    fieldnames = ["idx"]
                    for object_element in save_in_csv_attributes.values():
                        fieldnames.extend(list(object_element.keys()))
                        break
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for obj_idx, object_element in save_in_csv_attributes.items():
                        object_element["idx"] = obj_idx
                        writer.writerow(object_element)

        self._register_output("segmap_", "segmap", ".npy", "2.0.0")
        if save_in_csv_attributes is not None:
            self._register_output("class_inst_col_map",
                                  "segcolormap",
                                  ".csv",
                                  "2.0.0",
                                  unique_for_camposes=False,
                                  output_key_parameter_name="segcolormap_output_key",
                                  output_file_prefix_parameter_name="segcolormap_output_file_prefix")
