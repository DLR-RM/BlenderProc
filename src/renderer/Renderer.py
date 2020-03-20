import os
from sys import platform
import multiprocessing

import addon_utils
import bpy

from src.main.Module import Module
from src.utility.Utility import Utility
from src.utility.BlenderUtility import get_all_mesh_objects


class Renderer(Module):
    """
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "output_file_prefix", "The file prefix that should be used when writing the rendering to file."
       "output_key", "The key which should be used for storing the rendering in a merged file."

       "auto_tile_size", "If true, then the number of render tiles is set automatically using the render_auto_tile_size addon."
       "tile_x", "The number of separate render tiles to use along the x-axis. Ignored if auto_tile_size is set to true."
       "tile_y", "The number of separate render tiles to use along the y-axis. Ignored if auto_tile_size is set to true."
       "resolution_x", "The render image width."
       "resolution_y", "The render image height."
       "pixel_aspect_x", "The aspect ratio to use for the camera viewport. Can be different from the resolution aspect ratio to distort the image."
       "simplify_subdivision_render", "Global maximum subdivision level during rendering. Speeds up rendering."

       "samples", "Number of samples to render for each pixel."
       "denoiser", "The denoiser to use. Set to 'Blender', if the Blender's built-in denoiser should be used or set to 'Intel', if you want to use the Intel Open Image Denoiser.
       "max_bounces", "Total maximum number of bounces."
       "min_bounces", "Total minimum number of bounces."
       "glossy_bounces", "Maximum number of glossy reflection bounces, bounded by total maximum."
       "ao_bounces_render", "Approximate indirect light with background tinted ambient occlusion at the specified bounce."
       "transmission_bounces", "Maximum number of transmission bounces, bounded by total maximum."
       "volume_bounces", "Maximum number of volumetric scattering events"

       "render_depth", "If true, the depth is also rendered to file."
       "depth_output_file_prefix", "The file prefix that should be used when writing depth to file."
       "depth_output_key", "The key which should be used for storing the depth in a merged file."
       "depth_start", "Starting distance of the depth, measured from the camera."
       "depth_range", "Total distance in which the depth is measured, depth_end = depth_start + depth_range"
       "depth_falloff", "Type of transition used to fade depth. Default=Linear. [LINEAR, QUADRATIC, INVERSE_QUADRATIC]"

       "stereo", "If true, renders a pair of stereoscopic images for each camera position."
       "use_alpha", "If true, the alpha channel stored in .png textures is used."
    """

    DEPTH_END = 25.1

    def __init__(self, config):
        Module.__init__(self, config)
        self._avoid_rendering = config.get_bool("avoid_rendering", False)
        addon_utils.enable("render_auto_tile_size")

    def _configure_renderer(self, default_samples=256, default_denoiser="Blender"):
        """
         Sets many different render parameters which can be adjusted via the config.

         :param default_samples: Default number of samples to render for each pixel
        """
        bpy.context.scene.cycles.samples = self.config.get_int("samples", default_samples)

        if self.config.get_bool("auto_tile_size", True):
            bpy.context.scene.ats_settings.is_enabled = True
        else:
            bpy.context.scene.ats_settings.is_enabled = False
            bpy.context.scene.render.tile_x = self.config.get_int("tile_x")
            bpy.context.scene.render.tile_y = self.config.get_int("tile_y")

        # Set number of cpu cores used for rendering (1 thread is always used for coordination => 1 cpu thread means GPU-only rendering)
        number_of_threads = self.config.get_int("cpu_threads", 1)
        # If set to 0, use number of cores (default)
        if number_of_threads > 0:
            bpy.context.scene.render.threads_mode = "FIXED"
            bpy.context.scene.render.threads = number_of_threads
        
        # Collect camera and camera object
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data
        
        if not 'loaded_resolution' in cam:
            bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", 512)
            bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", 512)
            bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1)
        print('Resolution: {}, {}'.format(bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y))

        bpy.context.scene.render.resolution_percentage = 100
        # Lightning settings to reduce training time
        bpy.context.scene.render.engine = 'CYCLES'

        denoiser = self.config.get_string("denoiser", default_denoiser)
        if denoiser == "Intel":
            # The intel denoiser is activated via the compositor
            bpy.context.view_layer.cycles.use_denoising = False
            bpy.context.scene.use_nodes = True
            nodes = bpy.context.scene.node_tree.nodes
            links = bpy.context.scene.node_tree.links

            # The denoiser gets normal and diffuse color as input
            bpy.context.view_layer.use_pass_normal = True
            bpy.context.view_layer.use_pass_diffuse_color = True

            # Add denoiser node
            denoise_node = nodes.new("CompositorNodeDenoise")

            # Link nodes
            render_layer_node = nodes.get('Render Layers')
            composite_node = nodes.get('Composite')
            Utility.insert_node_instead_existing_link(links, render_layer_node.outputs['Image'], denoise_node.inputs['Image'], denoise_node.outputs['Image'], composite_node.inputs['Image'])

            links.new(render_layer_node.outputs['DiffCol'], denoise_node.inputs['Albedo'])
            links.new(render_layer_node.outputs['Normal'], denoise_node.inputs['Normal'])
        elif denoiser == "Blender":
            bpy.context.view_layer.cycles.use_denoising = True
        else:
            raise Exception("No such denoiser: " + denoiser)

        simplify_subdivision_render = self.config.get_int("simplify_subdivision_render", 3)
        if simplify_subdivision_render > 0:
            bpy.context.scene.render.use_simplify = True
            bpy.context.scene.render.simplify_subdivision_render = simplify_subdivision_render

        if platform == "darwin":
            # there is no gpu support in mac os so use the cpu with maximum power
            bpy.context.scene.cycles.device = "CPU"
            bpy.context.scene.render.threads = multiprocessing.cpu_count()
        else:
            bpy.context.scene.cycles.device = "GPU"
        bpy.context.scene.cycles.glossy_bounces = self.config.get_int("glossy_bounces", 0)
        bpy.context.scene.cycles.ao_bounces_render = self.config.get_int("ao_bounces_render", 3)
        bpy.context.scene.cycles.max_bounces = self.config.get_int("max_bounces", 3)
        bpy.context.scene.cycles.min_bounces = self.config.get_int("min_bounces", 1)
        bpy.context.scene.cycles.transmission_bounces = self.config.get_int("transmission_bounces", 0)
        bpy.context.scene.cycles.volume_bounces = self.config.get_int("volume_bounces", 0)

        bpy.context.scene.cycles.debug_bvh_type = "STATIC_BVH"
        bpy.context.scene.cycles.debug_use_spatial_splits = True
        # Setting use_persistent_data to True makes the rendering getting slower and slower (probably a blender bug)
        bpy.context.scene.render.use_persistent_data = False

        # Enable Stereoscopy
        bpy.context.scene.render.use_multiview = self.config.get_bool("stereo", False)
        if bpy.context.scene.render.use_multiview:
            bpy.context.scene.render.views_format = "STEREO_3D"

        self._use_alpha_channel = self.config.get_bool('use_alpha', False)

    def _write_depth_to_file(self):
        """ Configures the renderer, s.t. the z-values computed for the next rendering are directly written to file. """

        # Mist settings
        depth_start = self.config.get_float("depth_start", 0.1)
        depth_range = self.config.get_float("depth_range", 25.0)
        Renderer.DEPTH_END = depth_start + depth_range
        bpy.context.scene.world.mist_settings.start = depth_start
        bpy.context.scene.world.mist_settings.depth = depth_range
        bpy.context.scene.world.mist_settings.falloff = self.config.get_string("depth_falloff", "LINEAR")

        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        bpy.context.view_layer.use_pass_mist = True  # Enable depth pass

        tree = bpy.context.scene.node_tree
        links = tree.links

        # Use existing render layer
        render_layer_node = tree.nodes.get('Render Layers')
        # Create a mapper node to map from 0-1 to SI units
        mapper_node = tree.nodes.new("CompositorNodeMapRange")

        links.new(render_layer_node.outputs["Mist"], mapper_node.inputs['Value'])
        # map the values 0-1 to range depth_start to depth_range
        mapper_node.inputs['To Min'].default_value = depth_start
        mapper_node.inputs['To Max'].default_value = depth_start + depth_range

        output_file = tree.nodes.new("CompositorNodeOutputFile")
        output_file.base_path = self._determine_output_dir()
        output_file.format.file_format = "OPEN_EXR"
        output_file.file_slots.values()[0].path = self.config.get_string("depth_output_file_prefix", "depth_")

        # Feed the Mist output of the render layer to the input of the file IO layer
        links.new(mapper_node.outputs['Value'], output_file.inputs['Image'])

    def _render(self, default_prefix, custom_file_path=None):
        """ Renders each registered keypoint.

        :param default_prefix: The default prefix of the output files.
        """
        if self.config.get_bool("render_depth", False):
            self._write_depth_to_file()

        if custom_file_path is None:
            bpy.context.scene.render.filepath = os.path.join(self._determine_output_dir(), self.config.get_string("output_file_prefix", default_prefix))
        else:
            bpy.context.scene.render.filepath = custom_file_path

        # Skip if there is nothing to render
        if bpy.context.scene.frame_end != bpy.context.scene.frame_start:
            if len(get_all_mesh_objects()) == 0:
                raise Exception("There are no mesh-objects to render, "
                                "please load an object before invoking the renderer.")
            # As frame_end is pointing to the next free frame, decrease it by one, as blender will render all frames in [frame_start, frame_ned]
            bpy.context.scene.frame_end -= 1
            if not self._avoid_rendering:
                bpy.ops.render.render(animation=True, write_still=True)
            # Revert changes
            bpy.context.scene.frame_end += 1

    def add_alpha_channel_to_textures(self, blurry_edges):
        """
        Adds transparency to all textures, which contain an .png image as an image input

        :param blurry_edges: If True, the edges of the alpha channel might be blurry,
                             this causes errors if the alpha channel should only be 0 or 1

        Be careful, when you replace the original texture with something else (Segmentation, Normals, ...),
        the necessary texture node gets lost. By copying it into a new material as done in the NormalRenderer, you
        can keep the transparency even for those nodes.

        """
        if self._use_alpha_channel:
            obj_with_mats = [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]
            # walk over all objects, which have materials
            for obj in obj_with_mats:
                for slot in obj.material_slots:
                    texture_node = None
                    # check each node of the material
                    for node in slot.material.node_tree.nodes:
                        # if it is a texture image node
                        if 'TexImage' in node.bl_idname:
                            if '.png' in node.image.name: # contains an alpha channel
                                texture_node = node
                    # this material contains an alpha png texture
                    if texture_node is not None:
                        nodes = slot.material.node_tree.nodes
                        links = slot.material.node_tree.links
                        node_connected_to_the_output, material_output = \
                            Utility.get_node_connected_to_the_output_and_unlink_it(slot.material)

                        if node_connected_to_the_output is not None:
                            mix_node = nodes.new(type='ShaderNodeMixShader')

                            # avoid blurry edges on the edges important for Normal, SegMapRenderer and others
                            if blurry_edges:
                                # add the alpha channel of the image to the mix shader node as a factor
                                links.new(texture_node.outputs['Alpha'], mix_node.inputs['Fac'])
                            else:
                                bright_contrast_node = nodes.new("ShaderNodeBrightContrast")
                                # extreme high contrast to avoid blurry edges
                                bright_contrast_node.inputs['Contrast'].default_value = 1000.0
                                links.new(texture_node.outputs['Alpha'], bright_contrast_node.inputs['Color'])
                                links.new(bright_contrast_node.outputs['Color'], mix_node.inputs['Fac'])

                            links.new(node_connected_to_the_output.outputs[0], mix_node.inputs[2])
                            transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
                            links.new(transparent_node.outputs['BSDF'], mix_node.inputs[1])
                            # connect to material output
                            links.new(mix_node.outputs['Shader'], material_output.inputs['Surface'])
                        else:
                            raise Exception("Could not find shader node, which is connected to the material output for: {}".format(slot.name))

    def add_alpha_texture_node(self, used_material, new_material):
        """
        Adds to a predefined new_material a texture node from an existing material (used_material)
        This is necessary to connect it later on in the add_alpha_channel_to_textures
        :param used_material: existing material, which might contain a texture node with a .png texture
        :param new_material: a new material, which will get a copy of this texture node
        :return: the modified new_material, if no texture node was found, the original new_material
        """
        # find out if there is an .png file used here
        texture_node = None
        for node in used_material.node_tree.nodes:
            # if it is a texture image node
            if 'TexImage' in node.bl_idname:
                if '.png' in node.image.name: # contains an alpha channel
                    texture_node = node
        # this material contains an alpha png texture
        if texture_node is not None:
            new_mat_alpha = new_material.copy() # copy the material
            nodes = new_mat_alpha.node_tree.nodes
            # copy the texture node into the new material to make sure it is used
            new_tex_node = nodes.new(type='ShaderNodeTexImage')
            new_tex_node.image = texture_node.image
            # use the new material
            return new_mat_alpha
        return new_material

    def _register_output(self, default_prefix, default_key, suffix, version, unique_for_camposes=True, output_key_parameter_name="output_key", output_file_prefix_parameter_name="output_file_prefix"):
        """ Registers new output type using configured key and file prefix.

        If depth rendering is enabled, this will also register the corresponding depth output type.

        :param default_prefix: The default prefix of the generated files.
        :param default_key: The default key which should be used for storing the output in merged file.
        :param suffix: The suffix of the generated files.
        :param version: The version number which will be stored at key_version in the final merged file.
        :param unique_for_camposes: True if the registered output is unique for all the camera poses
        :param output_key_parameter_name: The parameter name to use for retrieving the output key from the config.
        :param output_file_prefix_parameter_name: The parameter name to use for retrieving the output file prefix from the config.
        """
        use_stereo = self.config.get_bool("stereo", False)

        super(Renderer, self)._register_output(default_prefix, default_key, suffix, version, stereo=use_stereo, unique_for_camposes=unique_for_camposes, output_key_parameter_name=output_key_parameter_name, output_file_prefix_parameter_name=output_file_prefix_parameter_name)

        if self.config.get_bool("render_depth", False):
            self._add_output_entry({
                "key": self.config.get_string("depth_output_key", "depth"),
                "path": os.path.join(self._determine_output_dir(), self.config.get_string("depth_output_file_prefix", "depth_")) + "%04d" + ".exr",
                "version": "2.0.0",
                "stereo": use_stereo
            })


