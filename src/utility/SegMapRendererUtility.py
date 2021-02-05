import csv
import os

import bpy
import numpy as np

from src.renderer.RendererInterface import RendererInterface
from src.utility.BlenderUtility import load_image, get_all_blender_mesh_objects
from src.utility.MaterialLoaderUtility import MaterialLoaderUtility
from src.utility.RendererUtility import RendererUtility
from src.utility.Utility import Utility


class SegMapRendererUtility:
    @staticmethod
    def _colorize_object(obj, color, use_alpha_channel):
        """ Adjusts the materials of the given object, s.t. they are ready for rendering the seg map.

        This is done by replacing all nodes just with an emission node, which emits the color corresponding to the
        category of the object.

        :param obj: The object to use.
        :param color: RGB array of a color in the range of [0, self.render_colorspace_size_per_dimension].
        :param use_alpha_channel: If true, the alpha channel stored in .png textures is used.
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
                if use_alpha_channel:
                    obj.data.materials[i] = MaterialLoaderUtility.add_alpha_texture_node(obj.material_slots[i].material, new_mat)
                else:
                    obj.data.materials[i] = new_mat
        else:
            obj.data.materials.append(new_mat)

    @staticmethod
    def _set_world_background_color(color):
        """ Set the background color of the blender world obejct.

        :param color: A 3-dim array containing the background color in range [0, 255]
        """
        nodes = bpy.context.scene.world.node_tree.nodes
        nodes.get("Background").inputs['Color'].default_value = color + [1]

    @staticmethod
    def _colorize_objects_for_instance_segmentation(objects, use_alpha_channel, render_colorspace_size_per_dimension):
        """ Sets a different color to each object.

        :param objects: A list of objects.
        :param use_alpha_channel: If true, the alpha channel stored in .png textures is used.
        :param render_colorspace_size_per_dimension: The limit of the colorspace to use per dimension for generating colors.
        :return: The num_splits_per_dimension of the spanned color space, the color map
        """
        # + 1 for the background
        colors, num_splits_per_dimension = Utility.generate_equidistant_values(len(objects) + 1, render_colorspace_size_per_dimension)
        # this list maps ids in the image back to the objects
        color_map = []

        # Set world background label, which is always label zero
        SegMapRendererUtility._set_world_background_color(colors[0])
        color_map.append(bpy.context.scene.world)  # add the world background as an object to this list

        for idx, obj in enumerate(objects):
            SegMapRendererUtility._colorize_object(obj, colors[idx + 1], use_alpha_channel)
            color_map.append(obj)

        return colors, num_splits_per_dimension, color_map

    @staticmethod
    def render(output_dir, temp_dir, used_attributes, used_default_values={}, file_prefix="segmap_", output_key="segmap", segcolormap_output_file_prefix="class_inst_col_map", segcolormap_output_key="segcolormap", use_alpha_channel=False, render_colorspace_size_per_dimension=2048):
        """ Renders segmentation maps for all frames.

        :param output_dir: The directory to write images to.
        :param temp_dir: The directory to write intermediate data to.
        :param used_attributes: The attributes to be used for color mapping.
        :param used_default_values: The default values used for the keys used in used_attributes.
        :param file_prefix: The prefix to use for writing the images.
        :param output_key: The key to use for registering the output.
        :param segcolormap_output_file_prefix: The prefix to use for writing the segmation-color map csv.
        :param segcolormap_output_key: The key to use for registering the segmation-color map output.
        :param use_alpha_channel: If true, the alpha channel stored in .png textures is used.
        :param render_colorspace_size_per_dimension: As we use float16 for storing the rendering, the interval of integers which can be precisely stored is [-2048, 2048]. As blender does not allow negative values for colors, we use [0, 2048] ** 3 as our color space which allows ~8 billion different colors/objects. This should be enough.
        """
        with Utility.UndoAfterExecution():
            RendererUtility.init()
            RendererUtility.set_samples(1)
            RendererUtility.set_adaptive_sampling(0)
            RendererUtility.set_denoiser(None)
            RendererUtility.set_light_bounces(1, 0, 0, 1, 0, 8, 0)

            # Get objects with meshes (i.e. not lights or cameras)
            objs_with_mats = get_all_blender_mesh_objects()

            colors, num_splits_per_dimension, used_objects = SegMapRendererUtility._colorize_objects_for_instance_segmentation(objs_with_mats, use_alpha_channel, render_colorspace_size_per_dimension)

            bpy.context.scene.cycles.filter_width = 0.0

            if use_alpha_channel:
                MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=False)

            # Determine path for temporary and for final output
            temporary_segmentation_file_path = os.path.join(temp_dir, "seg_")
            final_segmentation_file_path = os.path.join(output_dir, file_prefix)

            RendererUtility.set_output_format("OPEN_EXR", 16)
            RendererUtility.render(temp_dir, "seg_", None)

            # Find optimal dtype of output based on max index
            for dtype in [np.uint8, np.uint16, np.uint32]:
                optimal_dtype = dtype
                if np.iinfo(optimal_dtype).max >= len(colors) - 1:
                    break

            if 'class' in used_default_values:
                used_default_values['cp_category_id'] = used_default_values['class']

            if isinstance(used_attributes, str):
                # only one result is requested
                result_channels = 1
                used_attributes = [used_attributes]
            elif isinstance(used_attributes, list):
                result_channels = len(used_attributes)
            else:
                raise Exception("The type of this is not supported here: {}".format(used_attributes))

            save_in_csv_attributes = {}
            # define them for the avoid rendering case
            there_was_an_instance_rendering = False
            list_of_used_attributes = []

            # Check if stereo is enabled
            if bpy.context.scene.render.use_multiview:
                suffixes = ["_L", "_R"]
            else:
                suffixes = [""]

            # After rendering
            for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):  # for each rendered frame
                for suffix in suffixes:
                    file_path = temporary_segmentation_file_path + ("%04d" % frame) + suffix + ".exr"
                    segmentation = load_image(file_path)
                    print(file_path, segmentation.shape)

                    segmap = Utility.map_back_from_equally_spaced_equidistant_values(segmentation,
                                                                                     num_splits_per_dimension,
                                                                                     render_colorspace_size_per_dimension)
                    segmap = segmap.astype(optimal_dtype)

                    used_object_ids = np.unique(segmap)
                    max_id = np.max(used_object_ids)
                    if max_id >= len(used_objects):
                        raise Exception("There are more object colors than there are objects")
                    combined_result_map = []
                    there_was_an_instance_rendering = False
                    list_of_used_attributes = []
                    used_channels = []
                    for channel_id in range(result_channels):
                        resulting_map = np.empty((segmap.shape[0], segmap.shape[1]))
                        was_used = False
                        current_attribute = used_attributes[channel_id]
                        org_attribute = current_attribute

                        # if the class is used the category_id attribute is evaluated
                        if current_attribute == "class":
                            current_attribute = "cp_category_id"
                        # in the instance case the resulting ids are directly used
                        if current_attribute == "instance":
                            there_was_an_instance_rendering = True
                            resulting_map = segmap
                            was_used = True
                            # a non default value was also used
                            non_default_value_was_used = True
                        else:
                            if current_attribute != "cp_category_id":
                                list_of_used_attributes.append(current_attribute)
                            # for the current attribute remove cp_ and _csv, if present
                            used_attribute = current_attribute
                            if used_attribute.startswith("cp_"):
                                used_attribute = used_attribute[len("cp_"):]
                            # check if a default value was specified
                            default_value_set = False
                            if current_attribute in used_default_values or used_attribute in used_default_values:
                                default_value_set = True
                                if current_attribute in used_default_values:
                                    default_value = used_default_values[current_attribute]
                                elif used_attribute in used_default_values:
                                    default_value = used_default_values[used_attribute]
                            last_state_save_in_csv = None
                            # this avoids that for certain attributes only the default value is written
                            non_default_value_was_used = False
                            # iterate over all object ids
                            for object_id in used_object_ids:
                                is_default_value = False
                                # get the corresponding object via the id
                                current_obj = used_objects[object_id]
                                # if the current obj has a attribute with that name -> get it
                                if hasattr(current_obj, used_attribute):
                                    used_value = getattr(current_obj, used_attribute)
                                # if the current object has a custom property with that name -> get it
                                elif current_attribute.startswith("cp_") and used_attribute in current_obj:
                                    used_value = current_obj[used_attribute]
                                elif current_attribute.startswith("cf_"):
                                    if current_attribute == "cf_basename":
                                        used_value = current_obj.name
                                        if "." in used_value:
                                            used_value = used_value[:used_value.rfind(".")]
                                elif default_value_set:
                                    # if none of the above applies use the default value
                                    used_value = default_value
                                    is_default_value = True
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
                                    resulting_map[segmap == object_id] = used_value
                                    was_used = True
                                    if not is_default_value:
                                        non_default_value_was_used = True
                                    # save everything which is not instance also in the .csv
                                    if current_attribute != "instance":
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
                        if was_used and non_default_value_was_used:
                            used_channels.append(org_attribute)
                            combined_result_map.append(resulting_map)

                    fname = final_segmentation_file_path + ("%04d" % frame) + suffix
                    # combine all resulting images to one image
                    resulting_map = np.stack(combined_result_map, axis=2)
                    # remove the unneeded third dimension
                    if resulting_map.shape[2] == 1:
                        resulting_map = resulting_map[:, :, 0]
                    np.save(fname, resulting_map)

            if not there_was_an_instance_rendering:
                if len(list_of_used_attributes) > 0:
                    raise Exception("There were attributes specified in the may_by, which could not be saved as "
                                    "there was no \"instance\" may_by key used. This is true for this/these "
                                    "keys: {}".format(", ".join(list_of_used_attributes)))
                # if there was no instance rendering no .csv file is generated!
                # delete all saved infos about .csv
                save_in_csv_attributes = {}

            # write color mappings to file
            if save_in_csv_attributes:
                csv_file_path = os.path.join(output_dir, segcolormap_output_file_prefix + ".csv")
                with open(csv_file_path, 'w', newline='') as csvfile:
                    # get from the first element the used field names
                    fieldnames = ["idx"]
                    # get all used object element keys
                    for object_element in save_in_csv_attributes.values():
                        fieldnames.extend(list(object_element.keys()))
                        break
                    for channel_name in used_channels:
                        fieldnames.append("channel_{}".format(channel_name))
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    # save for each object all values in one row
                    for obj_idx, object_element in save_in_csv_attributes.items():
                        object_element["idx"] = obj_idx
                        for i, channel_name in enumerate(used_channels):
                            object_element["channel_{}".format(channel_name)] = i
                        writer.writerow(object_element)

        Utility.register_output(output_dir, file_prefix, output_key, ".npy", "2.0.0")
        if save_in_csv_attributes:
            Utility.register_output(output_dir,
                                    segcolormap_output_file_prefix,
                                    segcolormap_output_key,
                                    ".csv",
                                    "2.0.0",
                                    unique_for_camposes=False)
