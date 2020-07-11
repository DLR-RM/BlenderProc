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

    The SegMapRenderer can render segmetation maps of any kind, it can render any information related to each object.
    This can include an instance id, which is consistent over several key frames.
    It can also be a `category_id`, which can be indicated by "class".

    This Renderer can access all custom properties or attributes of the rendered objects.
    This means it can also be used to map your own custom properties to an image or if the data can not be stored in
    an image like the name of the object in a .csv file.

    The csv file will contain a mapping between each instance id and the corresponding custom property or attribute.

    Example 1:
        config: {
            "map_by": "class"
        }
        In this example each pixel would be mapped to the corresponding category_id of the object.
        Each object then needs such a custom property! Even the background. If an object is missing one an Exception
        is thrown.

    Example 2:
        "config": {
            "map_by": ["class", "instance"]
        }
        In this example the output will be a class image and an instance image, so the output will have two channels,
        instead of one. The first will contain the class the second the instance segmentation.

    Example 3:
        "config": {
            "map_by": ["class", "class_csv", "instance", "name"]
         }
         It is often useful to also store a mapping between the instance and these class in a dict, which is possible
         via the `_csv` option. All values which can not be stored in the image are stored inside of a dict. The `name`
         attribute would be saved now in a dict as we only store ints and floats in the image.
         We can force keys to be stored in the dict with adding "_csv" to the end.

    Example 4:
        "config": {
            "map_by": "class"
            "default_values": {"class": 0}
         }
         It is also possible to set default values, for keys object, which don't have a certain custom property.
         This is especially useful dealing with the background, which often lacks certain object properties.

    .. csv-table::
       :header: "Parameter", "Description"

       "map_by", "Method to be used for color mapping. Type: string. Default: "class".
                 "Available: [instance, class] or any custom property or attribute."
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
            if "category_id" not in obj:
                raise Exception("The object " + obj.name + " does not have a category_id.")

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

            # Find optimal dtype of output based on max index
            for dtype in [np.uint8, np.uint16, np.uint32]:
                optimal_dtype = dtype
                if np.iinfo(optimal_dtype).max >= len(colors) - 1:
                    break

            # get the type of mappings which should be performed
            used_attributes = self.config.get_raw_dict("map_by", "class")

            used_default_values = self.config.get_raw_dict("default_values", {})

            if isinstance(used_attributes, str):
                # only one result is requested
                result_channels = 1
                used_attributes = [used_attributes]
            elif isinstance(used_attributes, list):
                result_channels = len(used_attributes)
            else:
                raise Exception("The type of this is not supported here: {}".format(used_attributes))

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
                    max_id = np.max(used_object_ids)
                    if max_id >= len(used_objects):
                        raise Exception("There are more object colors than there are objects")
                    combined_result_map = []
                    for channel_id in range(result_channels):
                        resulting_map = np.empty((segmap.shape[0], segmap.shape[1]))
                        was_used = False
                        current_attribute = used_attributes[channel_id]

                        # if the class is used the category_id attribute is evaluated
                        if current_attribute == "class":
                            current_attribute = "cp_category_id"
                        if current_attribute == "class_csv":
                            current_attribute = "cp_category_id_csv"
                        # in the instance case the resulting ids are directly used
                        if current_attribute == "instance":
                            resulting_map = segmap
                            was_used = True
                        else:
                            # for the current attribute remove cp_ and _csv, if present
                            used_attribute = current_attribute
                            if used_attribute.startswith("cp_"):
                                used_attribute = used_attribute[len("cp_"):]
                            if used_attribute.endswith("_csv"):
                                used_attribute = used_attribute[:-len("_csv")]
                            # check if a default value was specified
                            default_value_set = False
                            if current_attribute in used_default_values or used_attribute in used_default_values:
                                default_value_set = True
                                if current_attribute in used_default_values:
                                    default_value = used_default_values[current_attribute]
                                elif used_attribute in used_default_values:
                                    default_value = used_default_values[used_attribute]
                            last_state_save_in_csv = None
                            # iterate over all object ids
                            for object_id in used_object_ids:
                                # get the corresponding object via the id
                                current_obj = used_objects[object_id]
                                # if the current obj has a attribute with that name -> get it
                                if hasattr(current_obj, used_attribute):
                                    used_value = getattr(current_obj, used_attribute)
                                # if the current object has a custom property with that name -> get it
                                elif current_attribute.startswith("cp_") and used_attribute in current_obj:
                                    used_value = current_obj[used_attribute]
                                elif default_value_set:
                                    # if none of the above applies use the default value
                                    used_value = default_value
                                else:
                                    # if the requested current_attribute is not a custom property or a attribute
                                    # or there is a default value stored
                                    # it throws an exception
                                    raise Exception("The obj: {} does not have the "
                                                    "attribute: {}, striped: {}. Maybe try a default "
                                                    "value.".format(current_obj.name, current_attribute, used_attribute))

                                # check if the value should be saved as an image or in the csv file
                                save_in_csv = False
                                try:
                                    if not current_attribute.endswith("_csv"):
                                        resulting_map[segmap == object_id] = used_value
                                        was_used = True
                                    else:
                                        save_in_csv = True
                                except ValueError:
                                    save_in_csv = True
                                if last_state_save_in_csv is not None and last_state_save_in_csv != save_in_csv:
                                    raise Exception("During creating the mapping, the saving to an image or a csv file "
                                                    "switched, this might indicated that the used default value, does "
                                                    "not have the same type as the returned value, "
                                                    "for: {}".format(current_attribute))
                                last_state_save_in_csv = save_in_csv
                                if save_in_csv:
                                    if object_id in save_in_csv_attributes:
                                        save_in_csv_attributes[object_id][used_attribute] = used_value
                                    else:
                                        save_in_csv_attributes[object_id] = {used_attribute: used_value}
                        if was_used:
                            combined_result_map.append(resulting_map)

                    fname = final_segmentation_file_path + "%04d" % frame
                    # combine all resulting images to one image
                    resulting_map = np.stack(combined_result_map, axis=2)
                    # remove the unneeded third dimension
                    if resulting_map.shape[2] == 1:
                        resulting_map = resulting_map[:, :, 0]
                    np.save(fname, resulting_map)

            # write color mappings to file
            if save_in_csv_attributes and not self._avoid_rendering:
                csv_file_path = os.path.join(self._determine_output_dir(),
                                             self.config.get_string("segcolormap_output_file_prefix",
                                                                    "class_inst_col_map") + ".csv")
                with open(csv_file_path, 'w', newline='') as csvfile:
                    # get from the first element the used field names
                    fieldnames = ["idx"]
                    # get all used object element keys
                    for object_element in save_in_csv_attributes.values():
                        fieldnames.extend(list(object_element.keys()))
                        break
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    # save for each object all values in one row
                    for obj_idx, object_element in save_in_csv_attributes.items():
                        object_element["idx"] = obj_idx
                        writer.writerow(object_element)

        self._register_output("segmap_", "segmap", ".npy", "2.0.0")
        if save_in_csv_attributes:
            self._register_output("class_inst_col_map",
                                  "segcolormap",
                                  ".csv",
                                  "2.0.0",
                                  unique_for_camposes=False,
                                  output_key_parameter_name="segcolormap_output_key",
                                  output_file_prefix_parameter_name="segcolormap_output_file_prefix")
