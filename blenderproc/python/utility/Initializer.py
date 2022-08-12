import os
import random
from numpy import random as np_random
from sys import platform

import multiprocessing

import bpy
import blenderproc.python.camera.CameraUtility as CameraUtility
from blenderproc.python.utility.DefaultConfig import DefaultConfig

import addon_utils

import blenderproc.python.renderer.RendererUtility as RendererUtility


def init():
    """ Initializes basic blender settings, the world and the camera.

    Also cleans up the whole scene at first.
    """
    cleanup()

    # Set language if necessary
    if bpy.context.preferences.view.language != "en_US":
        print("Setting blender language settings to english during this run")
        bpy.context.preferences.view.language = "en_US"

    # Use cycles
    bpy.context.scene.render.engine = 'CYCLES'

    # Set default render devices
    RendererUtility.set_render_devices()

    # setting the frame end, will be changed by the camera loader modules
    bpy.context.scene.frame_end = 0

    # Sets world default category id
    world = bpy.data.worlds['World']
    world["category_id"] = 0

    # Create the camera
    cam = bpy.data.cameras.new("Camera")
    cam_ob = bpy.data.objects.new("Camera", cam)
    bpy.context.scene.collection.objects.link(cam_ob)
    bpy.context.scene.camera = cam_ob

    Initializer.set_default_parameters()

    random_seed = os.getenv("BLENDER_PROC_RANDOM_SEED")
    if random_seed:
        print("Got random seed: {}".format(random_seed))
        try:
            random_seed = int(random_seed)
        except ValueError as e:
            raise e
        random.seed(random_seed)
        np_random.seed(random_seed)

def cleanup():
    """ Resets the scene to its clean state, but keeping the UI as it is """
    # Switch to right context
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')

    # Clean up
    Initializer._remove_all_data()
    Initializer._remove_custom_properties()

    # Create new world
    new_world = bpy.data.worlds.new("World")
    bpy.context.scene.world = new_world

class Initializer:

    @staticmethod
    def set_default_parameters():
        """ Loads and sets default parameters defined in DefaultConfig.py """
        # Set default intrinsics
        CameraUtility.set_intrinsics_from_blender_params(DefaultConfig.fov, DefaultConfig.resolution_x, DefaultConfig.resolution_y, 
                                                         DefaultConfig.clip_start, DefaultConfig.clip_end, DefaultConfig.pixel_aspect_x, 
                                                         DefaultConfig.pixel_aspect_y, DefaultConfig.shift_x, DefaultConfig.shift_y, DefaultConfig.lens_unit)
        CameraUtility.set_stereo_parameters(DefaultConfig.stereo_convergence_mode, DefaultConfig.stereo_convergence_distance, DefaultConfig.stereo_interocular_distance)

        # Init renderer
        RendererUtility._render_init()
        RendererUtility.set_world_background(DefaultConfig.world_background)
        RendererUtility.set_max_amount_of_samples(DefaultConfig.samples)
        RendererUtility.set_noise_threshold(DefaultConfig.sampling_noise_threshold)

        # Set number of cpu cores used for rendering (1 thread is always used for coordination => 1
        # cpu thread means GPU-only rendering)
        RendererUtility.set_cpu_threads(0)
        RendererUtility.set_denoiser(DefaultConfig.denoiser)

        RendererUtility.set_simplify_subdivision_render(DefaultConfig.simplify_subdivision_render)

        RendererUtility.set_light_bounces(DefaultConfig.diffuse_bounces,
                                          DefaultConfig.glossy_bounces,
                                          DefaultConfig.ao_bounces_render,
                                          DefaultConfig.max_bounces,
                                          DefaultConfig.transmission_bounces,
                                          DefaultConfig.transparency_bounces,
                                          DefaultConfig.volume_bounces)

        RendererUtility.set_output_format(DefaultConfig.file_format,
                                          DefaultConfig.color_depth,
                                          DefaultConfig.enable_transparency,
                                          DefaultConfig.jpg_quality)


    @staticmethod
    def _remove_all_data():
        """ Remove all data blocks except opened scripts and the default scene. """
        # Go through all attributes of bpy.data
        for collection in dir(bpy.data):
            data_structure = getattr(bpy.data, collection)
            # Check that it is a data collection
            if isinstance(data_structure, bpy.types.bpy_prop_collection) and hasattr(data_structure, "remove") and collection not in ["texts"]:
                # Go over all entities in that collection
                for block in data_structure:
                    # Remove everything besides the default scene
                    if not isinstance(block, bpy.types.Scene) or block.name != "Scene":
                        data_structure.remove(block)

    @staticmethod
    def _remove_custom_properties():
        """ Remove all custom properties registered at global entities like the scene. """
        for key in bpy.context.scene.keys():
            del bpy.context.scene[key]
