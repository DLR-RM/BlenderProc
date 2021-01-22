import os

import bpy

from src.main.GlobalStorage import GlobalStorage
from src.utility.BlenderUtility import get_all_mesh_objects
from src.utility.Utility import Utility
import mathutils
import math

class RendererUtility:

    @staticmethod
    def init():
        """ Initializes the renderer.

        This enables the cycles renderer and sets some options to speedup rendering.
        """
        bpy.context.scene.render.resolution_percentage = 100
        # Lightning settings to reduce training time
        bpy.context.scene.render.engine = 'CYCLES'

        bpy.context.scene.cycles.debug_bvh_type = "STATIC_BVH"
        bpy.context.scene.cycles.debug_use_spatial_splits = True
        # Setting use_persistent_data to True makes the rendering getting slower and slower (probably a blender bug)
        bpy.context.scene.render.use_persistent_data = False

    @staticmethod
    def _disable_all_denoiser():
        """ Disables all denoiser.

        At the moment this includes the cycles and the intel denoiser.
        """
        # Disable cycles denoiser
        bpy.context.view_layer.cycles.use_denoising = False

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

    @staticmethod
    def set_denoiser(denoiser):
        """ Enables the specified denoiser.

        Automatically disables all previously activated denoiser.

        :param denoiser: The name of the denoiser which should be enabled. Options are "INTEL", "BLENDER" and None. If None is given, then no denoiser will be active.
        """
        # Make sure there is no denoiser active
        RendererUtility._disable_all_denoiser()
        if denoiser is None:
            pass
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
        elif denoiser.upper() == "BLENDER":
            bpy.context.view_layer.cycles.use_denoising = True
        else:
            raise Exception("No such denoiser: " + denoiser)


    @staticmethod
    def set_light_bounces(diffuse_bounces, glossy_bounces, ao_bounces_render, max_bounces, transmission_bounces, transparent_max_bounces, volume_bounces):
        """ Sets the number of light bounces that should be used by the raytracing renderer.

        :param diffuse_bounces: Maximum number of diffuse reflection bounces, bounded by total maximum.
        :param glossy_bounces: Maximum number of glossy reflection bounces, bounded by total maximum.
        :param ao_bounces_render: Approximate indirect light with background tinted ambient occlusion at the specified bounce, 0 disables this feature.
        :param max_bounces: Total maximum number of bounces.
        :param transmission_bounces: Maximum number of transmission bounces, bounded by total maximum.
        :param transparent_max_bounces: Maximum number of transparent bounces.
        :param volume_bounces: Maximum number of volumetric scattering events.
        """
        bpy.context.scene.cycles.diffuse_bounces = diffuse_bounces
        bpy.context.scene.cycles.glossy_bounces = glossy_bounces
        bpy.context.scene.cycles.ao_bounces_render = ao_bounces_render
        bpy.context.scene.cycles.max_bounces = max_bounces
        bpy.context.scene.cycles.transmission_bounces = transmission_bounces
        bpy.context.scene.cycles.transparent_max_bounces = transparent_max_bounces
        bpy.context.scene.cycles.volume_bounces = volume_bounces


    @staticmethod
    def toggle_auto_tile_size(enable):
        """ Enables/Disables the automatic tile size detection via the render_auto_tile_size addon.

        :param enable: True, if it should be enabled.
        """
        bpy.context.scene.ats_settings.is_enabled = enable

    @staticmethod
    def set_tile_size(tile_x, tile_y):
        """ Sets the rendering tile size.

        This will automatically disable the automatic tile size detection.

        :param tile_x: The horizontal tile size in pixels.
        :param tile_y: The vertical tile size in pixels.
        """
        RendererUtility.toggle_auto_tile_size(False)
        bpy.context.scene.render.tile_x = tile_x
        bpy.context.scene.render.tile_y = tile_y

    @staticmethod
    def set_cpu_threads(num_threads):
        """ Sets the number of CPU cores to use simultaneously while rendering.

        :param num_threads: The number of threads to use. If 0 is given the number is automatically detected based on the cpu cores.
        """
        # If set to 0, use number of cores (default)
        if num_threads > 0:
            bpy.context.scene.render.threads_mode = "FIXED"
            bpy.context.scene.render.threads = num_threads
        else:
            bpy.context.scene.render.threads_mode = "AUTO"

    @staticmethod
    def toggle_stereo(enable):
        """ Enables/Disables stereoscopy.

        :param enable: True, if stereoscopy should be enabled.
        """
        bpy.context.scene.render.use_multiview = enable
        if enable:
            bpy.context.scene.render.views_format = "STEREO_3D"

    @staticmethod
    def set_simplify_subdivision_render(simplify_subdivision_render):
        """ Sets global maximum subdivision level during rendering to speedup rendering.

        :param simplify_subdivision_render: The maximum subdivision level. If 0 is given, simplification of scene is disabled.
        """
        if simplify_subdivision_render > 0:
            bpy.context.scene.render.use_simplify = True
            bpy.context.scene.render.simplify_subdivision_render = simplify_subdivision_render
        else:
            bpy.context.scene.render.use_simplify = False


    @staticmethod
    def set_adaptive_sampling(adaptive_threshold):
        """ Configures adaptive sampling.

        Adaptive sampling automatically decreases the number of samples per pixel based on estimated level of noise.

        :param adaptive_threshold: Noise level to stop sampling at. If 0 is given, adaptive sampling is disabled.
        """
        if adaptive_threshold > 0:
            bpy.context.scene.cycles.use_adaptive_sampling = True
            bpy.context.scene.cycles.adaptive_threshold = adaptive_threshold
        else:
            bpy.context.scene.cycles.use_adaptive_sampling = False

    @staticmethod
    def set_samples(samples):
        """ Sets the number of samples to render for each pixel.

        :param samples: The number of samples per pixel
        """
        bpy.context.scene.cycles.samples = samples

    @staticmethod
    def enable_distance_output(output_dir, file_prefix="distance_", output_key="distance", use_mist_as_distance=True, distance_start=0.1, distance_range=25.0, distance_falloff="LINEAR"):
        """ Enables writing distance images.

        Distance images will be written in the form of .exr files during the next rendering.

        :param output_dir: The directory to write files to.
        :param file_prefix: The prefix to use for writing the files.
        :param output_key: The key to use for registering the distance output.
        :param use_mist_as_distance: If true, the distance is sampled over several iterations, useful for motion blur or soft edges, if this is turned off, only one sample is taken to determine the depth. Default: True.
        :param distance_start: Starting distance of the distance, measured from the camera.
        :param distance_range: Total distance in which the distance is measured. distance_end = distance_start + distance_range.
        :param distance_falloff: Type of transition used to fade distance. Available: [LINEAR, QUADRATIC, INVERSE_QUADRATIC]
        """
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        GlobalStorage.add("renderer_distance_end", distance_start + distance_range)

        tree = bpy.context.scene.node_tree
        links = tree.links
        # Use existing render layer
        render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')

        # use either mist rendering or the z-buffer
        # mists uses an interpolation during the sample per pixel
        # while the z buffer only returns the closest object per pixel
        if use_mist_as_distance:
            bpy.context.scene.world.mist_settings.start = distance_start
            bpy.context.scene.world.mist_settings.depth = distance_range
            bpy.context.scene.world.mist_settings.falloff = distance_falloff

            bpy.context.view_layer.use_pass_mist = True  # Enable distance pass
            # Create a mapper node to map from 0-1 to SI units
            mapper_node = tree.nodes.new("CompositorNodeMapRange")
            links.new(render_layer_node.outputs["Mist"], mapper_node.inputs['Value'])
            # map the values 0-1 to range distance_start to distance_range
            mapper_node.inputs['To Min'].default_value = distance_start
            mapper_node.inputs['To Max'].default_value = distance_start + distance_range
            final_output = mapper_node.outputs['Value']
        else:
            bpy.context.view_layer.use_pass_z = True
            # add min and max nodes to perform the clipping to the desired range
            min_node = tree.nodes.new("CompositorNodeMath")
            min_node.operation = "MINIMUM"
            min_node.inputs[1].default_value = distance_start + distance_range
            links.new(render_layer_node.outputs["Depth"], min_node.inputs[0])
            max_node = tree.nodes.new("CompositorNodeMath")
            max_node.operation = "MAXIMUM"
            max_node.inputs[1].default_value = distance_start
            links.new(min_node.outputs["Value"], max_node.inputs[0])
            final_output = max_node.outputs["Value"]

        output_file = tree.nodes.new("CompositorNodeOutputFile")
        output_file.base_path = output_dir
        output_file.format.file_format = "OPEN_EXR"
        output_file.file_slots.values()[0].path = file_prefix

        # Feed the Z-Buffer or Mist output of the render layer to the input of the file IO layer
        links.new(final_output, output_file.inputs['Image'])

        Utility.add_output_entry({
            "key": output_key,
            "path": os.path.join(output_dir, file_prefix) + "%04d" + ".exr",
            "version": "2.0.0"
        })

    @staticmethod
    def enable_normals_output(output_dir, file_prefix="normals_", output_key="normals"):
        """ Enables writing normal images.

        Normal images will be written in the form of .exr files during the next rendering.

        :param output_dir: The directory to write files to.
        :param file_prefix: The prefix to use for writing the files.
        :param output_key: The key to use for registering the normal output.
        """
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
        multiplication_values = [[], [], []]
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
        cam_ob = bpy.context.scene.camera
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            bpy.context.scene.frame_set(frame)
            used_rotation_matrix = cam_ob.matrix_world @ rot_around_x_axis
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

    @staticmethod
    def map_file_format_to_file_ending(file_format):
        """ Returns the files endings for a given blender output format.

        :param file_format: The blender file format.
        :return: The file ending.
        """
        if file_format == 'PNG':
            return ".png"
        elif file_format == 'JPEG':
            return ".jpg"
        elif file_format == 'OPEN_EXR':
            return ".exr"
        else:
            raise Exception("Unknown Image Type " + file_format)

    @staticmethod
    def render(output_dir, file_prefix="rgb_", output_key="colors"):
        """ Render all frames.

        This will go through all frames from scene.frame_start to scene.frame_end and render each of them.

        :param output_dir: The directory to write images to.
        :param file_prefix: The prefix to use for writing the images.
        :param output_key: The key to use for registering the output.
        """
        if output_key is not None:
            Utility.add_output_entry({
                "key": output_key,
                "path": os.path.join(output_dir, file_prefix) + "%04d" + RendererUtility.map_file_format_to_file_ending(bpy.context.scene.render.image_settings.file_format),
                "version": "2.0.0"
            })

        bpy.context.scene.render.filepath = os.path.join(output_dir, file_prefix)

        # Skip if there is nothing to render
        if bpy.context.scene.frame_end != bpy.context.scene.frame_start:
            if len(get_all_mesh_objects()) == 0:
                raise Exception("There are no mesh-objects to render, "
                                "please load an object before invoking the renderer.")
            # As frame_end is pointing to the next free frame, decrease it by one, as
            # blender will render all frames in [frame_start, frame_ned]
            bpy.context.scene.frame_end -= 1
            bpy.ops.render.render(animation=True, write_still=True)
            # Revert changes
            bpy.context.scene.frame_end += 1

    @staticmethod
    def set_output_format(file_format, color_depth=8, enable_transparency=False, jpg_quality=95):
        """ Sets the output format to use for rendering.

        :param file_format: The file format to use, e.q. "PNG", "JPEG" or "OPEN_EXR".
        :param color_depth: The color depth.
        :param enable_transparency: If true, the output will contain a alpha channel and the background will be set transparent.
        :param jpg_quality: The quality to use, if file format is set to "JPEG".
        """
        # In case a previous renderer changed these settings
        # Store as RGB by default unless the user specifies store_alpha as true in yaml
        bpy.context.scene.render.image_settings.color_mode = "RGBA" if enable_transparency else "RGB"
        # set the background as transparent if transparent_background is true in yaml
        bpy.context.scene.render.film_transparent = enable_transparency
        bpy.context.scene.render.image_settings.file_format = file_format
        bpy.context.scene.render.image_settings.color_depth = str(color_depth)

        # only influences jpg quality
        bpy.context.scene.render.image_settings.quality = jpg_quality

    @staticmethod
    def enable_motion_blur(motion_blur_length=0.5, rolling_shutter_type="NONE", rolling_shutter_length=0.1):
        """ Enables motion blur and sets rolling shutter.

        :param motion_blur_length: Time taken in frames between shutter open and close.
        :param rolling_shutter_type: Type of rolling shutter effect. If "NONE", rolling shutter is disabled.
        :param rolling_shutter_length: Scanline "exposure" time for the rolling shutter effect.
        """
        bpy.context.scene.render.use_motion_blur = True
        bpy.context.scene.render.motion_blur_shutter = motion_blur_length

        bpy.context.scene.cycles.rolling_shutter_type = rolling_shutter_type
        bpy.context.scene.cycles.rolling_shutter_duration = rolling_shutter_length

