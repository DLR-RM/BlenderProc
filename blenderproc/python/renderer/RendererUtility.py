"""Provides functionality to render a color, normal, depth and distance image."""

from contextlib import contextmanager
import os
import threading
from typing import IO, Union, Dict, List, Set, Optional, Any
import math
import sys
import platform
import time

import mathutils
import bpy
import numpy as np
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn

from blenderproc.python.camera import CameraUtility
from blenderproc.python.utility.GlobalStorage import GlobalStorage
from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects
from blenderproc.python.utility.DefaultConfig import DefaultConfig
from blenderproc.python.utility.Utility import Utility, stdout_redirected
from blenderproc.python.writer.WriterUtility import _WriterUtility


def set_denoiser(denoiser: Optional[str]):
    """ Enables the specified denoiser.

    Automatically disables all previously activated denoiser.

    :param denoiser: The name of the denoiser which should be enabled. Options are "INTEL", "OPTIX" and None. \
                     If None is given, then no denoiser will be active.
    """
    # Make sure there is no denoiser active
    disable_all_denoiser()
    if denoiser is None:
        pass
    elif denoiser.upper() == "OPTIX":
        bpy.context.scene.cycles.use_denoising = True
        bpy.context.view_layer.cycles.use_denoising = True
        bpy.context.scene.cycles.denoiser = "OPTIX"
    elif denoiser.upper() == "INTEL":
        # The intel denoiser is activated via the compositor
        bpy.context.scene.use_nodes = True
        nodes = bpy.context.scene.node_tree.nodes
        links = bpy.context.scene.node_tree.links

        # The denoiser gets normal and diffuse color as input
        bpy.context.view_layer.use_pass_normal = True
        bpy.context.view_layer.use_pass_diffuse_color = True

        # Add denoiser node
        denoise_node = nodes.new("CompositorNodeDenoise")

        # Link nodes
        render_layer_node = Utility.get_the_one_node_with_type(nodes, 'CompositorNodeRLayers')
        composite_node = Utility.get_the_one_node_with_type(nodes, 'CompositorNodeComposite')
        Utility.insert_node_instead_existing_link(links,
                                                  render_layer_node.outputs['Image'],
                                                  denoise_node.inputs['Image'],
                                                  denoise_node.outputs['Image'],
                                                  composite_node.inputs['Image'])

        links.new(render_layer_node.outputs['DiffCol'], denoise_node.inputs['Albedo'])
        links.new(render_layer_node.outputs['Normal'], denoise_node.inputs['Normal'])
    else:
        raise Exception("No such denoiser: " + denoiser)


def set_light_bounces(diffuse_bounces: Optional[int] = None, glossy_bounces: Optional[int] = None,
                      ao_bounces_render: Optional[int] = None, max_bounces: Optional[int] = None,
                      transmission_bounces: Optional[int] = None, transparent_max_bounces: Optional[int] = None,
                      volume_bounces: Optional[int] = None):
    """
    Sets the number of light bounces that should be used by the raytracing renderer.
    Default values are defined in DefaultConfig.py

    :param diffuse_bounces: Maximum number of diffuse reflection bounces, bounded by total maximum.
    :param glossy_bounces: Maximum number of glossy reflection bounces, bounded by total maximum.
    :param ao_bounces_render: Approximate indirect light with background tinted ambient occlusion at the \
                              specified bounce, 0 disables this feature.
    :param max_bounces: Total maximum number of bounces.
    :param transmission_bounces: Maximum number of transmission bounces, bounded by total maximum.
    :param transparent_max_bounces: Maximum number of transparent bounces.
    :param volume_bounces: Maximum number of volumetric scattering events.
    """
    if diffuse_bounces is not None:
        bpy.context.scene.cycles.diffuse_bounces = diffuse_bounces
    if glossy_bounces is not None:
        bpy.context.scene.cycles.glossy_bounces = glossy_bounces
    if ao_bounces_render is not None:
        bpy.context.scene.cycles.ao_bounces_render = ao_bounces_render
    if max_bounces is not None:
        bpy.context.scene.cycles.max_bounces = max_bounces
    if transmission_bounces is not None:
        bpy.context.scene.cycles.transmission_bounces = transmission_bounces
    if transparent_max_bounces is not None:
        bpy.context.scene.cycles.transparent_max_bounces = transparent_max_bounces
    if volume_bounces is not None:
        bpy.context.scene.cycles.volume_bounces = volume_bounces


def set_cpu_threads(num_threads: int):
    """ Sets the number of CPU cores to use simultaneously while rendering.

    :param num_threads: The number of threads to use. If 0 is given the number is automatically detected based
                        on the cpu cores.
    """
    # If set to 0, use number of cores (default)
    if num_threads > 0:
        bpy.context.scene.render.threads_mode = "FIXED"
        bpy.context.scene.render.threads = num_threads
    else:
        bpy.context.scene.render.threads_mode = "AUTO"


def toggle_stereo(enable: bool):
    """ Enables/Disables stereoscopy.

    :param enable: True, if stereoscopy should be enabled.
    """
    bpy.context.scene.render.use_multiview = enable
    if enable:
        bpy.context.scene.render.views_format = "STEREO_3D"

def toggle_light_tree(enable: bool):
    """ Enables/Disables blender's light tree for rendering.

    Enabling the light tree reduces the noise in scenes with many point lights,
    however it increases the render time per sample.
    See https://wiki.blender.org/wiki/Reference/Release_Notes/3.5/Cycles

    :param enable: True, if light tree should be enabled.
    """
    bpy.context.scene.cycles.use_light_tree = enable

def set_simplify_subdivision_render(simplify_subdivision_render: int):
    """ Sets global maximum subdivision level during rendering to speedup rendering.

    :param simplify_subdivision_render: The maximum subdivision level. If 0 is given, simplification of scene
                                        is disabled.
    """
    if simplify_subdivision_render > 0:
        bpy.context.scene.render.use_simplify = True
        bpy.context.scene.render.simplify_subdivision_render = simplify_subdivision_render
    else:
        bpy.context.scene.render.use_simplify = False


def set_noise_threshold(noise_threshold: float):
    """ Configures the adaptive sampling, the noise threshold is typically between 0.1 and 0.001.
    Adaptive sampling automatically decreases the number of samples per pixel based on estimated level of noise.

    We do not recommend setting the noise threshold value to zero and therefore turning off the adaptive sampling.

    For more information see the official documentation:
    https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html#adaptive-sampling

    :param noise_threshold: Noise level to stop sampling at. If 0 is given, adaptive sampling is disabled and only the
                            max amount of samples is used.
    """
    if noise_threshold > 0:
        bpy.context.scene.cycles.use_adaptive_sampling = True
        bpy.context.scene.cycles.adaptive_threshold = noise_threshold
    else:
        bpy.context.scene.cycles.use_adaptive_sampling = False


def set_max_amount_of_samples(samples: int):
    """ Sets the maximum number of samples to render for each pixel.
    This maximum amount is usually not reached if the noise threshold is low enough.
    If the noise threshold was set to 0, then only the maximum number of samples is used (We do not recommend this).

    :param samples: The maximum number of samples per pixel
    """
    bpy.context.scene.cycles.samples = samples


def enable_distance_output(activate_antialiasing: bool, output_dir: Optional[str] = None,
                           file_prefix: str = "distance_",
                           output_key: str = "distance", antialiasing_distance_max: float = None,
                           convert_to_depth: bool = False):
    """ Enables writing distance images.


    :param activate_antialiasing: If this is True the final image will be anti-aliased
    :param output_dir: The directory to write files to, if this is None the temporary directory is used.
    :param file_prefix: The prefix to use for writing the files.
    :param output_key: The key to use for registering the distance output.
    :param antialiasing_distance_max: Max distance in which the distance is measured. Resolution decreases
                                      antiproportionally. Only if activate_antialiasing is True.
    :param convert_to_depth: If this is true, while loading a postprocessing step is executed to convert this distance
                             image to a depth image
    """
    if not activate_antialiasing:
        return enable_depth_output(activate_antialiasing, output_dir, file_prefix, output_key, convert_to_distance=True)
    if output_dir is None:
        output_dir = Utility.get_temporary_directory()
    if antialiasing_distance_max is None:
        antialiasing_distance_max = DefaultConfig.antialiasing_distance_max

    if GlobalStorage.is_in_storage("distance_output_is_enabled"):
        msg = "The distance enable function can not be called twice. Either you called it twice or you used the " \
              "enable_depth_output with activate_antialiasing=True, which internally calls this function. This is " \
              "currently not supported, but there is an easy way to solve this, you can use the " \
              "bproc.postprocessing.dist2depth and depth2dist function on the output of the renderer and generate " \
              "the antialiased depth image yourself."
        raise RuntimeError(msg)
    GlobalStorage.add("distance_output_is_enabled", True)

    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True
    GlobalStorage.add("renderer_distance_end", antialiasing_distance_max)

    tree = bpy.context.scene.node_tree
    links = tree.links
    # Use existing render layer
    render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')

    # Set mist pass limits
    bpy.context.scene.world.mist_settings.start = 0
    bpy.context.scene.world.mist_settings.depth = antialiasing_distance_max
    bpy.context.scene.world.mist_settings.falloff = "LINEAR"

    bpy.context.view_layer.use_pass_mist = True  # Enable distance pass
    # Create a mapper node to map from 0-1 to SI units
    mapper_node = tree.nodes.new("CompositorNodeMapRange")
    links.new(render_layer_node.outputs["Mist"], mapper_node.inputs['Value'])
    # map the values 0-1 to range distance_start to distance_range
    mapper_node.inputs['From Max'].default_value = 1.0
    mapper_node.inputs['To Min'].default_value = 0
    mapper_node.inputs['To Max'].default_value = antialiasing_distance_max
    final_output = mapper_node.outputs['Value']

    # Build output node
    output_file = tree.nodes.new("CompositorNodeOutputFile")
    output_file.base_path = output_dir
    output_file.format.file_format = "OPEN_EXR"
    output_file.file_slots.values()[0].path = file_prefix

    # Feed the Z-Buffer or Mist output of the render layer to the input of the file IO layer
    links.new(final_output, output_file.inputs['Image'])

    Utility.add_output_entry({
        "key": output_key,
        "path": os.path.join(output_dir, file_prefix) + "%04d" + ".exr",
        "version": "2.0.0",
        "trim_redundant_channels": True,
        "convert_to_depth": convert_to_depth
    })
    return None


def enable_depth_output(activate_antialiasing: bool, output_dir: Optional[str] = None, file_prefix: str = "depth_",
                        output_key: str = "depth", antialiasing_distance_max: float = None,
                        convert_to_distance: bool = False):
    """ Enables writing depth images.

    Depth images will be written in the form of .exr files during the next rendering.

    :param activate_antialiasing: If this is True the final image will be antialiased
    :param output_dir: The directory to write files to, if this is None the temporary directory is used.
    :param file_prefix: The prefix to use for writing the files.
    :param output_key: The key to use for registering the depth output.
    :param antialiasing_distance_max: Max distance in which the distance is measured. \
                                      Only if activate_antialiasing is True.
    :param convert_to_distance: If this is true, while loading a postprocessing step is executed to convert this depth \
                                image to a distance image
    """
    if activate_antialiasing:
        return enable_distance_output(activate_antialiasing, output_dir, file_prefix, output_key,
                                      antialiasing_distance_max, convert_to_depth=True)
    if output_dir is None:
        output_dir = Utility.get_temporary_directory()

    if GlobalStorage.is_in_storage("depth_output_is_enabled"):
        msg = "The depth enable function can not be called twice. Either you called it twice or you used the " \
              "enable_distance_output with activate_antialiasing=False, which internally calls this function. This " \
              "is currently not supported, but there is an easy way to solve this, you can use the " \
              "bproc.postprocessing.dist2depth and depth2dist function on the output of the renderer and generate " \
              "the antialiased distance image yourself."
        raise RuntimeError(msg)
    GlobalStorage.add("depth_output_is_enabled", True)

    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True

    tree = bpy.context.scene.node_tree
    links = tree.links
    # Use existing render layer
    render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')

    # Enable z-buffer pass
    bpy.context.view_layer.use_pass_z = True

    # Build output node
    output_file = tree.nodes.new("CompositorNodeOutputFile")
    output_file.base_path = output_dir
    output_file.format.file_format = "OPEN_EXR"
    output_file.file_slots.values()[0].path = file_prefix

    # Feed the Z-Buffer output of the render layer to the input of the file IO layer
    links.new(render_layer_node.outputs["Depth"], output_file.inputs['Image'])

    Utility.add_output_entry({
        "key": output_key,
        "path": os.path.join(output_dir, file_prefix) + "%04d" + ".exr",
        "version": "2.0.0",
        "trim_redundant_channels": True,
        "convert_to_distance": convert_to_distance
    })
    return None


def enable_normals_output(output_dir: Optional[str] = None, file_prefix: str = "normals_",
                          output_key: str = "normals"):
    """ Enables writing normal images.

    Normal images will be written in the form of .exr files during the next rendering.

    :param output_dir: The directory to write files to, if this is None the temporary directory is used.
    :param file_prefix: The prefix to use for writing the files.
    :param output_key: The key to use for registering the normal output.
    """
    if output_dir is None:
        output_dir = Utility.get_temporary_directory()

    bpy.context.view_layer.use_pass_normal = True
    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links

    # Use existing render layer
    render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')

    separate_rgba = tree.nodes.new("CompositorNodeSepRGBA")
    space_between_nodes_x = 200
    space_between_nodes_y = -300
    separate_rgba.location.x = space_between_nodes_x
    separate_rgba.location.y = space_between_nodes_y
    links.new(render_layer_node.outputs["Normal"], separate_rgba.inputs["Image"])

    combine_rgba = tree.nodes.new("CompositorNodeCombRGBA")
    combine_rgba.location.x = space_between_nodes_x * 14

    c_channels = ["R", "G", "B"]
    offset = space_between_nodes_x * 2
    multiplication_values: List[List[bpy.types.Node]] = [[], [], []]
    channel_results = {}
    for row_index, channel in enumerate(c_channels):
        # matrix multiplication
        mulitpliers = []
        for column in range(3):
            multiply = tree.nodes.new("CompositorNodeMath")
            multiply.operation = "MULTIPLY"
            multiply.inputs[1].default_value = 0  # setting at the end for all frames
            multiply.location.x = column * space_between_nodes_x + offset
            multiply.location.y = row_index * space_between_nodes_y
            links.new(separate_rgba.outputs[c_channels[column]], multiply.inputs[0])
            mulitpliers.append(multiply)
            multiplication_values[row_index].append(multiply)

        first_add = tree.nodes.new("CompositorNodeMath")
        first_add.operation = "ADD"
        first_add.location.x = space_between_nodes_x * 5 + offset
        first_add.location.y = row_index * space_between_nodes_y
        links.new(mulitpliers[0].outputs["Value"], first_add.inputs[0])
        links.new(mulitpliers[1].outputs["Value"], first_add.inputs[1])

        second_add = tree.nodes.new("CompositorNodeMath")
        second_add.operation = "ADD"
        second_add.location.x = space_between_nodes_x * 6 + offset
        second_add.location.y = row_index * space_between_nodes_y
        links.new(first_add.outputs["Value"], second_add.inputs[0])
        links.new(mulitpliers[2].outputs["Value"], second_add.inputs[1])

        channel_results[channel] = second_add

    # set the matrix accordingly
    rot_around_x_axis = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'X')
    for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
        used_rotation_matrix = CameraUtility.get_camera_pose(frame) @ rot_around_x_axis
        for row_index in range(3):
            for column_index in range(3):
                current_multiply = multiplication_values[row_index][column_index]
                current_multiply.inputs[1].default_value = used_rotation_matrix[column_index][row_index]
                current_multiply.inputs[1].keyframe_insert(data_path='default_value', frame=frame)
    offset = 8 * space_between_nodes_x
    for index, channel in enumerate(c_channels):
        multiply = tree.nodes.new("CompositorNodeMath")
        multiply.operation = "MULTIPLY"
        multiply.location.x = space_between_nodes_x * 2 + offset
        multiply.location.y = index * space_between_nodes_y
        links.new(channel_results[channel].outputs["Value"], multiply.inputs[0])
        if channel == "G":
            multiply.inputs[1].default_value = -0.5
        else:
            multiply.inputs[1].default_value = 0.5
        add = tree.nodes.new("CompositorNodeMath")
        add.operation = "ADD"
        add.location.x = space_between_nodes_x * 3 + offset
        add.location.y = index * space_between_nodes_y
        links.new(multiply.outputs["Value"], add.inputs[0])
        add.inputs[1].default_value = 0.5
        output_channel = channel
        if channel == "G":
            output_channel = "B"
        elif channel == "B":
            output_channel = "G"
        links.new(add.outputs["Value"], combine_rgba.inputs[output_channel])

    output_file = tree.nodes.new("CompositorNodeOutputFile")
    output_file.base_path = output_dir
    output_file.format.file_format = "OPEN_EXR"
    output_file.file_slots.values()[0].path = file_prefix
    output_file.location.x = space_between_nodes_x * 15
    links.new(combine_rgba.outputs["Image"], output_file.inputs["Image"])

    Utility.add_output_entry({
        "key": output_key,
        "path": os.path.join(output_dir, file_prefix) + "%04d" + ".exr",
        "version": "2.0.0"
    })


def enable_segmentation_output(map_by: Union[str, List[str]] = "category_id",
                               default_values: Optional[Dict[str, Any]] = None,
                               pass_alpha_threshold: float = 0.05,
                               output_dir: Optional[str] = None,
                               file_prefix: str = "segmap_", output_key: str = "segmap"):
    """ Enables segmentation output by certain keys.

    The key instances is used, if a mapping of every object in the scene to an integer is requested. These integers
    are assigned randomly and do not follow any system. They are consisted for one rendering call.

    By default, the custom property `category_id` is used. It has to be set for every visible object in the scene,
    including the background (world). One can provide a `default_value` for it to avoid errors: `{"category_id": 0}`.

    Map by keys can be all custom properties or the attributes of an object such as `location` or `name`. If the value
    can not be stored in the image itself an instance image has to be generated. The output then will contain a
    dictionary mapping the instance ids to the attributes of the objects.

    :param map_by: Map by keys, either a single str or a list of str.
    :param default_values: A dictionary offering a default value for objects which do not provide a value
                           for a certain key
    :param pass_alpha_threshold: This alpha threshold is used to decide which object to use a low value means that an
                                 object has to be nearly completely transparent to be considered transparent, while
                                 materials such as frosted class with an alpha value of 0.5 would be considered opaque
    :param output_dir: The temporary output dir in which the resulting .exr images are saved
    :param file_prefix: The prefix to use for writing the files.
    :param output_key: The key to use for registering the segmentation output.
    """
    # give all objects an id, background is always zero
    for index, obj in enumerate(get_all_blender_mesh_objects()):
        obj.pass_index = index + 1

    # add the pass object index id to the rendering output
    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True
    bpy.context.scene.view_layers["ViewLayer"].use_pass_object_index = True

    tree = bpy.context.scene.node_tree
    links = tree.links

    render_layer_node = tree.nodes.get('Render Layers')

    if output_dir is None:
        output_dir = Utility.get_temporary_directory()

    output_node = tree.nodes.new('CompositorNodeOutputFile')
    output_node.base_path = output_dir
    output_node.format.file_format = "OPEN_EXR"
    output_node.file_slots.values()[0].path = file_prefix
    Utility.add_output_entry({
        "key": output_key,
        "path": os.path.join(output_dir, file_prefix) + "%04d" + ".exr",
        "version": "3.0.0",
        "trim_redundant_channels": True,
        "is_semantic_segmentation": True,
        "semantic_segmentation_mapping": map_by,
        "semantic_segmentation_default_values": default_values
    })

    links.new(render_layer_node.outputs["IndexOB"], output_node.inputs["Image"])

    # set the threshold low to avoid noise in alpha materials
    bpy.context.scene.view_layers["ViewLayer"].pass_alpha_threshold = pass_alpha_threshold


def enable_diffuse_color_output(output_dir: Optional[str] = None, file_prefix: str = "diffuse_",
                                output_key: str = "diffuse"):
    """ Enables writing diffuse color (albedo) images.

    Diffuse color images will be written in the form of .png files during the next rendering.

    :param output_dir: The directory to write files to, if this is None the temporary directory is used.
    :param file_prefix: The prefix to use for writing the files.
    :param output_key: The key to use for registering the diffuse color output.
    """
    if output_dir is None:
        output_dir = Utility.get_temporary_directory()

    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links

    bpy.context.view_layer.use_pass_diffuse_color = True
    render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')
    final_output = render_layer_node.outputs["DiffCol"]

    output_file = tree.nodes.new('CompositorNodeOutputFile')
    output_file.base_path = output_dir
    output_file.format.file_format = "PNG"
    output_file.file_slots.values()[0].path = file_prefix
    links.new(final_output, output_file.inputs['Image'])

    Utility.add_output_entry({
        "key": output_key,
        "path": os.path.join(output_dir, file_prefix) + "%04d" + ".png",
        "version": "2.0.0"
    })


def map_file_format_to_file_ending(file_format: str) -> str:
    """ Returns the files endings for a given blender output format.

    :param file_format: The blender file format.
    :return: The file ending.
    """
    if file_format == 'PNG':
        return ".png"
    if file_format == 'JPEG':
        return ".jpg"
    if file_format == 'OPEN_EXR':
        return ".exr"
    raise RuntimeError(f"Unknown Image Type {file_format}")


def _progress_bar_thread(pipe_out: int, stdout: IO, total_frames: int, num_samples: int):
    """ The thread rendering the progress bar

    :param pipe_out: The pipe output delivering blenders debug messages.
    :param stdout: The stdout to which the progress bar should be written.
    :param total_frames: The number of frames that should be rendered.
    :param num_samples: The number of samples used to render each frame.
    """
    # Define columns for progress bar
    columns = [
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        TextColumn("[progress.description]{task.fields[status]}"),
    ]
    # Initializes progress bar using given stdout
    with Progress(*columns, console=Console(file=stdout), transient=True) as progress:
        complete_task = progress.add_task("[green]Total", total=total_frames, status="")
        frame_task = progress.add_task("[yellow]Current frame", total=num_samples, status="")

        # Continuously read blenders debug messages
        current_line = ""
        starting_frame_number = bpy.context.scene.frame_start
        while True:
            # Read the next character
            char = os.read(pipe_out, 1)
            if not char:
                break
            char = chr(char[0])
            # If its the ending character, stop
            if not char or "\b" == char:
                break
            # If the current line has ended
            if char == "\n":
                # Check if its a line we can use (starts with "Fra:")
                if current_line.startswith("Fra:"):
                    # Extract current frame number and use it to set the progress bar
                    frame_number = int(current_line.split()[0][len("Fra:"):])
                    frames_completed = frame_number - starting_frame_number
                    progress.update(complete_task, completed=frames_completed)
                    progress.update(complete_task, status=f"Rendering frame {frames_completed + 1} of {total_frames}")

                    # Split line into columns
                    status_columns = [col.strip() for col in current_line.split("|")]
                    if "Scene, ViewLayer" in status_columns:
                        # If we are currently at "Scene, ViewLayer", use everything afterwards
                        status = " | ".join(status_columns[status_columns.index("Scene, ViewLayer") + 1:])
                        # If we are currently rendering, update the progress
                        if status.startswith("Sample"):
                            progress.update(frame_task, completed=int(status[len("Sample"):].split("/", maxsplit=1)[0]))
                    elif "Compositing" in status_columns:
                        # If we are at "Compositing", use everything afterwards including "Compositing"
                        status = " | ".join(status_columns[status_columns.index("Compositing"):])
                        # Set render progress to complete
                        progress.update(frame_task, completed=num_samples)
                    else:
                        # In every other case, use last column
                        status = status_columns[-1]
                    # Set status to progress bar
                    progress.update(frame_task, status=status)
                # Start with next line
                current_line = ""
            else:
                # Append char to current line
                current_line += char


@contextmanager
def _render_progress_bar(pipe_out: int, pipe_in: int, stdout: IO, total_frames: int, enabled: bool = True):
    """ Shows a progress bar visualizing the render progress.

    :param pipe_out: The pipe output delivering blenders debug messages.
    :param pipe_in: The input of the pipe, necessary to send the end character.
    :param stdout: The stdout to which the progress bar should be written.
    :param total_frames: The number of frames that should be rendered.
    :param enabled: If False, no progress bar is shown.
    """
    if enabled:
        thread = threading.Thread(target=_progress_bar_thread,
                                  args=(pipe_out, stdout, total_frames, bpy.context.scene.cycles.samples))
        thread.start()
        try:
            yield
        finally:
            # Send final character, so the thread knows to stop
            w = os.fdopen(pipe_in, 'w')
            w.write("\b")
            w.close()
            thread.join()
    else:
        yield


def render(output_dir: Optional[str] = None, file_prefix: str = "rgb_", output_key: Optional[str] = "colors",
           load_keys: Optional[Set[str]] = None, return_data: bool = True,
           keys_with_alpha_channel: Optional[Set[str]] = None,
           verbose: bool = False) -> Dict[str, Union[np.ndarray, List[np.ndarray]]]:
    """ Render all frames.

    This will go through all frames from scene.frame_start to scene.frame_end and render each of them.

    :param output_dir: The directory to write files to, if this is None the temporary directory is used. \
                       The temporary directory is usually in the shared memory (only true for linux).
    :param file_prefix: The prefix to use for writing the images.
    :param output_key: The key to use for registering the output.
    :param load_keys: Set of output keys to load when available
    :param return_data: Whether to load and return generated data.
    :param keys_with_alpha_channel: A set containing all keys whose alpha channels should be loaded.
    :param verbose: If True, more details about the rendering process are printed.
    :return: dict of lists of raw renderer output. Keys can be 'distance', 'colors', 'normals'
    """
    if output_dir is None:
        output_dir = Utility.get_temporary_directory()
    if load_keys is None:
        load_keys = {'colors', 'distance', 'normals', 'diffuse', 'depth', 'segmap'}
        keys_with_alpha_channel = {'colors'} if bpy.context.scene.render.film_transparent else None

    if output_key is not None:
        Utility.add_output_entry({
            "key": output_key,
            "path": os.path.join(output_dir, file_prefix) + "%04d" +
                    map_file_format_to_file_ending(bpy.context.scene.render.image_settings.file_format),
            "version": "2.0.0"
        })
        load_keys.add(output_key)

    bpy.context.scene.render.filepath = os.path.join(output_dir, file_prefix)

    # Skip if there is nothing to render
    if bpy.context.scene.frame_end != bpy.context.scene.frame_start:
        if len(get_all_blender_mesh_objects()) == 0:
            raise Exception("There are no mesh-objects to render, "
                            "please load an object before invoking the renderer.")
        # Print what is rendered
        total_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start
        if load_keys:
            registered_output_keys = [output["key"] for output in Utility.get_registered_outputs()]
            keys_to_render = sorted([key for key in load_keys if key in registered_output_keys])
            print(f"Rendering {total_frames} frames of {', '.join(keys_to_render)}...")

        # As frame_end is pointing to the next free frame, decrease it by one, as
        # blender will render all frames in [frame_start, frame_ned]
        bpy.context.scene.frame_end -= 1

        # Define pipe to communicate blenders debug messages to progress bar
        pipe_out, pipe_in = os.pipe()
        begin = time.time()
        with stdout_redirected(pipe_in, enabled=not verbose) as stdout:
            with _render_progress_bar(pipe_out, pipe_in, stdout, total_frames, enabled=not verbose):
                bpy.ops.render.render(animation=True, write_still=True)

        # Close Pipes to prevent having unclosed file handles
        try:
            os.close(pipe_out)
        except OSError:
            pass
        try:
            os.close(pipe_in)
        except OSError:
            pass

        print(f"Finished rendering after {time.time() - begin:.3f} seconds")
        # Revert changes
        bpy.context.scene.frame_end += 1
    else:
        raise RuntimeError("No camera poses have been registered, therefore nothing can be rendered. A camera "
                           "pose can be registered via bproc.camera.add_camera_pose().")

    return _WriterUtility.load_registered_outputs(load_keys, keys_with_alpha_channel) if return_data else {}


def set_output_format(file_format: Optional[str] = None, color_depth: Optional[int] = None,
                      enable_transparency: Optional[bool] = None, jpg_quality: Optional[int] = None):
    """ Sets the output format to use for rendering. Default values defined in DefaultConfig.py.

    :param file_format: The file format to use, e.q. "PNG", "JPEG" or "OPEN_EXR".
    :param color_depth: The color depth.
    :param enable_transparency: If true, the output will contain a alpha channel and the background will be
                                set transparent.
    :param jpg_quality: The quality to use, if file format is set to "JPEG".
    """
    if enable_transparency is not None:
        # In case a previous renderer changed these settings
        # Store as RGB by default unless the user specifies store_alpha as true in yaml
        bpy.context.scene.render.image_settings.color_mode = "RGBA" if enable_transparency else "RGB"
        # set the background as transparent if transparent_background is true in yaml
        bpy.context.scene.render.film_transparent = enable_transparency
    if file_format is not None:
        bpy.context.scene.render.image_settings.file_format = file_format
    if color_depth is not None:
        bpy.context.scene.render.image_settings.color_depth = str(color_depth)
    if jpg_quality is not None:
        # only influences jpg quality
        bpy.context.scene.render.image_settings.quality = jpg_quality


def enable_motion_blur(motion_blur_length: float = 0.5, rolling_shutter_type: str = "NONE",
                       rolling_shutter_length: float = 0.1):
    """ Enables motion blur and sets rolling shutter.

    :param motion_blur_length: Time taken in frames between shutter open and close.
    :param rolling_shutter_type: Type of rolling shutter effect. If "NONE", rolling shutter is disabled.
    :param rolling_shutter_length: Scanline "exposure" time for the rolling shutter effect.
    """
    bpy.context.scene.render.use_motion_blur = True
    bpy.context.scene.render.motion_blur_shutter = motion_blur_length

    bpy.context.scene.cycles.rolling_shutter_type = rolling_shutter_type
    bpy.context.scene.cycles.rolling_shutter_duration = rolling_shutter_length


def render_init():
    """ Initializes the renderer.

    This enables the cycles renderer and sets some options to speedup rendering.
    """
    bpy.context.scene.render.resolution_percentage = 100
    # Lightning settings to reduce training time
    bpy.context.scene.render.engine = 'CYCLES'

    bpy.context.scene.cycles.debug_bvh_type = "STATIC_BVH"
    bpy.context.scene.cycles.debug_use_spatial_splits = True
    # Setting use_persistent_data to True makes the rendering getting slower and slower (probably a blender bug)
    bpy.context.scene.render.use_persistent_data = True


def disable_all_denoiser():
    """ Disables all denoiser.

    At the moment this includes the cycles and the intel denoiser.
    """
    # Disable cycles denoiser
    bpy.context.view_layer.cycles.use_denoising = False
    bpy.context.scene.cycles.use_denoising = False

    # Disable intel denoiser
    if bpy.context.scene.use_nodes:
        nodes = bpy.context.scene.node_tree.nodes
        links = bpy.context.scene.node_tree.links

        # Go through all existing denoiser nodes
        for denoiser_node in Utility.get_nodes_with_type(nodes, 'CompositorNodeDenoise'):
            in_node = denoiser_node.inputs['Image']
            out_node = denoiser_node.outputs['Image']

            # If it is fully included into the node tree
            if in_node.is_linked and out_node.is_linked:
                # There is always only one input link
                in_link = in_node.links[0]
                # Connect from_socket of the incoming link with all to_sockets of the out going links
                for link in out_node.links:
                    links.new(in_link.from_socket, link.to_socket)

            # Finally remove the denoiser node
            nodes.remove(denoiser_node)


def set_world_background(color: List[float], strength: float = 1):
    """ Sets the color of blenders world background

    :param color: A three-dimensional list specifying the new color in floats.
    :param strength: The strength of the emitted background light.
    """
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Unlink any incoming link that would overwrite the default value
    if len(nodes.get("Background").inputs['Color'].links) > 0:
        links.remove(nodes.get("Background").inputs['Color'].links[0])

    nodes.get("Background").inputs['Strength'].default_value = strength
    nodes.get("Background").inputs['Color'].default_value = color + [1]


def enable_experimental_features():
    """ Enables experimental cycles features. """
    bpy.context.scene.cycles.feature_set = 'EXPERIMENTAL'


def set_render_devices(use_only_cpu: bool = False, desired_gpu_device_type: Union[str, List[str]] = None,
                       desired_gpu_ids: Union[int, List[int]] = None):
    """ Configures the devices to use for rendering.

    :param use_only_cpu: If True, only the cpu is used for rendering.
    :param desired_gpu_device_type: One or multiple GPU device types to consider. If multiple are given,
                                    the first available is used. Possible choices are ["OPTIX", "CUDA",
                                    "METAL", "HIP"]. Default is ["OPTIX", "CUDA", "HIP"] on linux/windows and
                                    ["METAL"] on supported Mac devices.
    :param desired_gpu_ids: One or multiple GPU ids to specifically use. If none is given, all suitable GPUs are used.
    """
    # Mark beginning of selection to avoid confusion when calling set_render_devices multiple times:
    print("Selecting render devices...")

    if desired_gpu_device_type is None:
        # If no gpu types are specified, use the default types based on the OS
        if sys.platform == "darwin":
            mac_version = platform.mac_ver()[0]
            mac_version_numbers = [int(ele) for ele in mac_version.split(".")]
            # On recent macs, use METAL, otherwise use cpu only
            if (mac_version_numbers[0] == 12 and mac_version_numbers[1] >= 3) or mac_version_numbers[0] > 12:
                desired_gpu_device_type = ["METAL"]
            else:
                desired_gpu_device_type = []
        else:
            # Define default for linux and windows
            desired_gpu_device_type = ["OPTIX", "CUDA", "HIP"]
    elif not isinstance(desired_gpu_device_type, list):
        # Make sure it's a list
        desired_gpu_device_type = [desired_gpu_device_type]

    # Make sure desired_gpu_device_type is a list
    if desired_gpu_ids is not None and not isinstance(desired_gpu_ids, list):
        desired_gpu_ids = [desired_gpu_ids]

    # Decide between gpu and cpu rendering
    if not desired_gpu_device_type or use_only_cpu:
        # Use only CPU
        bpy.context.scene.cycles.device = "CPU"
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = "NONE"
        print("Using only the CPU for rendering")
    else:
        # Use GPU
        bpy.context.scene.cycles.device = "GPU"
        preferences = bpy.context.preferences.addons['cycles'].preferences

        # Go over all specified device types
        found = False
        for device_type in desired_gpu_device_type:
            # Check if there are devices that support that type
            devices = preferences.get_devices_for_type(device_type)
            if devices:
                # Set device type
                bpy.context.preferences.addons['cycles'].preferences.compute_device_type = device_type
                # Go over all devices with that type
                found = False
                for i, device in enumerate(devices):
                    # Only use gpus with specified ids
                    if desired_gpu_ids is None or i in desired_gpu_ids:
                        print(f"Device {device.name} of type {device.type} found and used.")
                        device.use = True
                        found = True
                    else:
                        device.use = False

                if not found:
                    raise RuntimeError(f"The specified gpu ids lead to no selected gpu at all. Valid gpu ids are "
                                       f"{list(range(len(devices)))}")

                break

        if not found:
            bpy.context.scene.cycles.device = "CPU"
            bpy.context.preferences.addons['cycles'].preferences.compute_device_type = "NONE"
            print("Using only the CPU for rendering")
