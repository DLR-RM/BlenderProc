import csv
import os
from typing import List, Tuple, Union, Dict, Optional, Any

import bpy
import mathutils
import numpy as np

from blenderproc.python.utility.BlenderUtility import load_image, get_all_blender_mesh_objects
from blenderproc.python.material import MaterialLoaderUtility
import blenderproc.python.renderer.RendererUtility as RendererUtility
from blenderproc.python.utility.Utility import Utility


def render_segmap(output_dir: Optional[str] = None, temp_dir: Optional[str] = None,
                  map_by: Union[str, List[str]] = "class",
                  default_values: Optional[Dict[str, int]] = None, file_prefix: str = "segmap_",
                  output_key: str = "segmap", segcolormap_output_file_prefix: str = "instance_attribute_map_",
                  segcolormap_output_key: str = "segcolormap", use_alpha_channel: bool = False,
                  render_colorspace_size_per_dimension: int = 2048) -> \
        Dict[str, Union[np.ndarray, List[np.ndarray]]]:
    """ Renders segmentation maps for all frames

    :param output_dir: The directory to write images to.
    :param temp_dir: The directory to write intermediate data to.
    :param map_by: The attributes to be used for color mapping.
    :param default_values: The default values used for the keys used in attributes, if None is {"class": 0}.
    :param file_prefix: The prefix to use for writing the images.
    :param output_key: The key to use for registering the output.
    :param segcolormap_output_file_prefix: The prefix to use for writing the segmentation-color map csv.
    :param segcolormap_output_key: The key to use for registering the segmentation-color map output.
    :param use_alpha_channel: If true, the alpha channel stored in .png textures is used.
    :param render_colorspace_size_per_dimension: As we use float16 for storing the rendering, the interval of \
                                                 integers which can be precisely stored is [-2048, 2048]. As \
                                                 blender does not allow negative values for colors, we use \
                                                 [0, 2048] ** 3 as our color space which allows ~8 billion \
                                                 different colors/objects. This should be enough.
    :return: dict of lists of segmaps and (for instance segmentation) segcolormaps
    """

    if output_dir is None:
        output_dir = Utility.get_temporary_directory()
    if temp_dir is None:
        temp_dir = Utility.get_temporary_directory()
    if default_values is None:
        default_values = {"class": 0}

    with Utility.UndoAfterExecution():
        RendererUtility._render_init()
        RendererUtility.set_samples(1)
        RendererUtility.set_adaptive_sampling(0)
        RendererUtility.set_denoiser(None)
        RendererUtility.set_light_bounces(1, 0, 0, 1, 0, 8, 0)

        attributes = map_by
        if 'class' in default_values:
            default_values['cp_category_id'] = default_values['class']

        # Get objects with meshes (i.e. not lights or cameras)
        objs_with_mats = get_all_blender_mesh_objects()

        colors, num_splits_per_dimension, objects = _colorize_objects_for_instance_segmentation(objs_with_mats,
                                                                                                use_alpha_channel,
                                                                                                render_colorspace_size_per_dimension)

        bpy.context.scene.cycles.filter_width = 0.0

        if use_alpha_channel:
            MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=False)

        # Determine path for temporary and for final output
        temporary_segmentation_file_path = os.path.join(temp_dir, "seg_")
        final_segmentation_file_path = os.path.join(output_dir, file_prefix)

        RendererUtility.set_output_format("OPEN_EXR", 16)
        RendererUtility.render(temp_dir, "seg_", None, return_data=False)

        # Find optimal dtype of output based on max index
        for dtype in [np.uint8, np.uint16, np.uint32]:
            optimal_dtype = dtype
            if np.iinfo(optimal_dtype).max >= len(colors) - 1:
                break

        if isinstance(attributes, str):
            # only one result is requested
            result_channels = 1
            attributes = [attributes]
        elif isinstance(attributes, list):
            result_channels = len(attributes)
        else:
            raise Exception("The type of this is not supported here: {}".format(attributes))

        # define them for the avoid rendering case
        there_was_an_instance_rendering = False
        list_of_attributes: List[str] = []

        # Check if stereo is enabled
        if bpy.context.scene.render.use_multiview:
            suffixes = ["_L", "_R"]
        else:
            suffixes = [""]

        return_dict: Dict[str, Union[np.ndarray, List[np.ndarray]]] = {}

        # After rendering
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):  # for each rendered frame
            save_in_csv_attributes: Dict[int, Dict[str, Any]] = {}
            for suffix in suffixes:
                file_path = temporary_segmentation_file_path + ("%04d" % frame) + suffix + ".exr"
                segmentation = load_image(file_path)
                print(file_path, segmentation.shape)

                segmap = Utility.map_back_from_equally_spaced_equidistant_values(segmentation,
                                                                                 num_splits_per_dimension,
                                                                                 render_colorspace_size_per_dimension)
                segmap = segmap.astype(optimal_dtype)

                object_ids = np.unique(segmap)
                max_id = np.max(object_ids)
                if max_id >= len(objects):
                    raise Exception("There are more object colors than there are objects")
                combined_result_map = []
                there_was_an_instance_rendering = False
                list_of_attributes = []
                channels = []
                for channel_id in range(result_channels):
                    num_default_values = 0
                    resulting_map = np.zeros((segmap.shape[0], segmap.shape[1]), dtype=optimal_dtype)
                    was_used = False
                    current_attribute = attributes[channel_id]
                    org_attribute = current_attribute

                    # if the class is used the category_id attribute is evaluated
                    if current_attribute == "class":
                        current_attribute = "cp_category_id"
                    # in the instance case the resulting ids are directly used
                    if current_attribute == "instance":
                        there_was_an_instance_rendering = True
                        resulting_map = segmap
                        was_used = True
                    else:
                        if current_attribute != "cp_category_id":
                            list_of_attributes.append(current_attribute)
                        # for the current attribute remove cp_ and _csv, if present
                        attribute = current_attribute
                        if attribute.startswith("cp_"):
                            attribute = attribute[len("cp_"):]
                        # check if a default value was specified
                        default_value_set = False
                        if current_attribute in default_values or attribute in default_values:
                            default_value_set = True
                            if current_attribute in default_values:
                                default_value = default_values[current_attribute]
                            elif attribute in default_values:
                                default_value = default_values[attribute]                        
                        # iterate over all object ids
                        for object_id in object_ids:
                            # Convert np.uint8 to int, such that the save_in_csv_attributes dict can later be serialized
                            object_id = int(object_id)
                            # get the corresponding object via the id
                            current_obj = objects[object_id]
                            # if the current obj has a attribute with that name -> get it
                            if hasattr(current_obj, attribute):
                                value = getattr(current_obj, attribute)
                            # if the current object has a custom property with that name -> get it
                            elif current_attribute.startswith("cp_") and attribute in current_obj:
                                value = current_obj[attribute]
                            elif current_attribute.startswith("cf_"):
                                if current_attribute == "cf_basename":
                                    value = current_obj.name
                                    if "." in value:
                                        value = value[:value.rfind(".")]
                            elif default_value_set:
                                # if none of the above applies use the default value
                                value = default_value
                                num_default_values += 1
                            else:
                                # if the requested current_attribute is not a custom property or a attribute
                                # or there is a default value stored
                                # it throws an exception
                                raise Exception("The obj: {} does not have the "
                                                "attribute: {}, striped: {}. Maybe try a default "
                                                "value.".format(current_obj.name, current_attribute, attribute))
                            
                            # save everything which is not instance also in the .csv
                            if isinstance(value, (int, float, np.integer, np.floating)):
                                was_used = True
                                resulting_map[segmap == object_id] = value

                            if object_id in save_in_csv_attributes:
                                save_in_csv_attributes[object_id][attribute] = value
                            else:
                                save_in_csv_attributes[object_id] = {attribute: value}
                                
                    if was_used and num_default_values < len(object_ids):
                        channels.append(org_attribute)
                        combined_result_map.append(resulting_map)
                        return_dict.setdefault("{}_segmaps{}".format(org_attribute, suffix), []).append(resulting_map)

                fname = final_segmentation_file_path + ("%04d" % frame) + suffix
                # combine all resulting images to one image
                resulting_map = np.stack(combined_result_map, axis=2)
                # remove the unneeded third dimension
                if resulting_map.shape[2] == 1:
                    resulting_map = resulting_map[:, :, 0]
                # TODO: Remove unnecessary save when we give up backwards compatibility
                np.save(fname, resulting_map)

            if there_was_an_instance_rendering:
                mappings = []
                for object_id, attribute_dict in save_in_csv_attributes.items():
                    mappings.append({"idx": object_id, **attribute_dict})
                return_dict.setdefault("instance_attribute_maps", []).append(mappings)

                # write color mappings to file
                # TODO: Remove unnecessary csv file when we give up backwards compatibility
                csv_file_path = os.path.join(output_dir, segcolormap_output_file_prefix + ("%04d.csv" % frame))
                with open(csv_file_path, 'w', newline='') as csvfile:
                    # get from the first element the used field names
                    fieldnames = ["idx"]
                    # get all used object element keys
                    for object_element in save_in_csv_attributes.values():
                        fieldnames.extend(list(object_element.keys()))
                        break
                    for channel_name in channels:
                        fieldnames.append("channel_{}".format(channel_name))
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    # save for each object all values in one row
                    for obj_idx, object_element in save_in_csv_attributes.items():
                        object_element["idx"] = obj_idx
                        for i, channel_name in enumerate(channels):
                            object_element["channel_{}".format(channel_name)] = i
                        writer.writerow(object_element)
            else:
                if len(list_of_attributes) > 0:
                    raise Exception("There were attributes specified in the may_by, which could not be saved as "
                                    "there was no \"instance\" may_by key used. This is true for this/these "
                                    "keys: {}".format(", ".join(list_of_attributes)))
                # if there was no instance rendering no .csv file is generated!
                # delete all saved infos about .csv
                save_in_csv_attributes = {}

    Utility.register_output(output_dir, file_prefix, output_key, ".npy", "2.0.0")

    if save_in_csv_attributes:
        Utility.register_output(output_dir,
                                segcolormap_output_file_prefix,
                                segcolormap_output_key,
                                ".csv",
                                "2.0.0")
    return return_dict


def _colorize_object(obj: bpy.types.Object, color: mathutils.Vector, use_alpha_channel: bool):
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
                obj.data.materials[i] = MaterialLoaderUtility.add_alpha_texture_node(obj.material_slots[i].material,
                                                                                     new_mat)
            else:
                obj.data.materials[i] = new_mat
    else:
        obj.data.materials.append(new_mat)


def _set_world_background_color(color: mathutils.Vector):
    """ Set the background color of the blender world object.

    :param color: A 3-dim array containing the background color in range [0, 255]
    """
    nodes = bpy.context.scene.world.node_tree.nodes
    links = bpy.context.scene.world.node_tree.links

    # Unlink any incoming link that would overwrite the default value
    if len(nodes.get("Background").inputs['Color'].links) > 0:
        links.remove(nodes.get("Background").inputs['Color'].links[0])
    # Set strength to 1 as it would act as a multiplier
    nodes.get("Background").inputs['Strength'].default_value = 1
    nodes.get("Background").inputs['Color'].default_value = color + [1]


def _colorize_objects_for_instance_segmentation(objects: List[bpy.types.Object], use_alpha_channel: bool,
                                                render_colorspace_size_per_dimension: int) \
        -> Tuple[List[List[int]], int, List[bpy.types.Object]]:
    """ Sets a different color to each object.

    :param objects: A list of objects.
    :param use_alpha_channel: If true, the alpha channel stored in .png textures is used.
    :param render_colorspace_size_per_dimension: The limit of the colorspace to use per dimension for generating colors.
    :return: The num_splits_per_dimension of the spanned color space, the color map
    """
    # + 1 for the background
    colors, num_splits_per_dimension = Utility.generate_equidistant_values(len(objects) + 1,
                                                                           render_colorspace_size_per_dimension)
    # this list maps ids in the image back to the objects
    color_map = []

    # Set world background label, which is always label zero
    _set_world_background_color(colors[0])
    color_map.append(bpy.context.scene.world)  # add the world background as an object to this list

    for idx, obj in enumerate(objects):
        _colorize_object(obj, colors[idx + 1], use_alpha_channel)
        color_map.append(obj)

    return colors, num_splits_per_dimension, color_map
