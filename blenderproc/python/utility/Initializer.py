""" This module provides functions to init a BlenderProc scene. """

import os
import random

from numpy import random as np_random
import bpy

from blenderproc.python.utility.GlobalStorage import GlobalStorage
from blenderproc.python.utility.Utility import reset_keyframes
from blenderproc.python.camera import CameraUtility
from blenderproc.python.utility.DefaultConfig import DefaultConfig
from blenderproc.python.renderer import RendererUtility


def init(clean_up_scene: bool = True):
    """ Initializes BlenderProc.

    Cleans up the whole scene at first and then initializes basic blender settings, the world, the renderer and
    the camera. This method should only be called once in the beginning. If you want to clean up the scene afterwards,
    use bproc.clean_up()

    :param clean_up_scene: Set to False, if you want to keep all scene data.
    """
    # Check if init has already been run
    if GlobalStorage.is_in_storage("bproc_init_complete") and GlobalStorage.get("bproc_init_complete"):
        raise RuntimeError("BlenderProc has already been initialized via bproc.init(), this should not be done twice. "
                           "If you want to clean up the scene, use bproc.clean_up().")

    if clean_up_scene:
        clean_up(clean_up_camera=True)

    # Set language if necessary
    if bpy.context.preferences.view.language != "en_US":
        print("Setting blender language settings to english during this run")
        bpy.context.preferences.view.language = "en_US"

    # Use cycles
    bpy.context.scene.render.engine = 'CYCLES'

    # Set default render devices
    RendererUtility.set_render_devices()

    # Set default parameters
    _Initializer.set_default_parameters()

    random_seed = os.getenv("BLENDER_PROC_RANDOM_SEED")
    if random_seed:
        print(f"Got random seed: {random_seed}")
        try:
            random_seed = int(random_seed)
        except ValueError as e:
            raise e
        random.seed(random_seed)
        np_random.seed(random_seed)

    # Remember init was completed
    GlobalStorage.add("bproc_init_complete", True)


def clean_up(clean_up_camera: bool = False):
    """ Resets the scene to its clean state.

    This method removes all objects, camera poses and cleans up the world background.
    All (renderer) settings and the UI are kept as they are.

    :param clean_up_camera: If True, also the camera is set back to its clean state.
    """
    # Switch to right context
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')

    # Clean up
    _Initializer.remove_all_data(clean_up_camera)
    _Initializer.remove_custom_properties()

    # Create new world
    new_world = bpy.data.worlds.new("World")
    bpy.context.scene.world = new_world
    new_world["category_id"] = 0

    if clean_up_camera:
        # Create the camera
        cam = bpy.data.cameras.new("Camera")
        cam_ob = bpy.data.objects.new("Camera", cam)
        bpy.context.scene.collection.objects.link(cam_ob)
        bpy.context.scene.camera = cam_ob

    # Make sure keyframes are cleaned up
    reset_keyframes()


class _Initializer:
    """
    This is the initializer class used to init a BlenderProc scene.
    """

    @staticmethod
    def set_default_parameters():
        """ Loads and sets default parameters defined in DefaultConfig.py """
        # Set default intrinsics
        CameraUtility.set_intrinsics_from_blender_params(DefaultConfig.fov, DefaultConfig.resolution_x,
                                                         DefaultConfig.resolution_y, DefaultConfig.clip_start,
                                                         DefaultConfig.clip_end, DefaultConfig.pixel_aspect_x,
                                                         DefaultConfig.pixel_aspect_y, DefaultConfig.shift_x,
                                                         DefaultConfig.shift_y, DefaultConfig.lens_unit)
        CameraUtility.set_stereo_parameters(DefaultConfig.stereo_convergence_mode,
                                            DefaultConfig.stereo_convergence_distance,
                                            DefaultConfig.stereo_interocular_distance)

        # Init renderer
        RendererUtility.render_init()
        RendererUtility.set_world_background(DefaultConfig.world_background)
        RendererUtility.set_max_amount_of_samples(DefaultConfig.samples)
        RendererUtility.set_noise_threshold(DefaultConfig.sampling_noise_threshold)

        # Set number of cpu cores used for rendering (1 thread is always used for coordination => 1
        # cpu thread means GPU-only rendering)
        RendererUtility.set_cpu_threads(0)
        RendererUtility.set_denoiser(DefaultConfig.denoiser)
        # For now disable the light tree per default, as it seems to increase render time for most of our tests
        RendererUtility.toggle_light_tree(False)

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
    def remove_all_data(remove_camera: bool = True):
        """ Remove all data blocks except opened scripts, the default scene and the camera.

        :param remove_camera: If True, also the default camera is removed.
        """
        # Go through all attributes of bpy.data
        for collection in dir(bpy.data):
            data_structure = getattr(bpy.data, collection)
            # Check that it is a data collection
            if isinstance(data_structure, bpy.types.bpy_prop_collection) and hasattr(data_structure, "remove") \
                    and collection not in ["texts"]:
                # Go over all entities in that collection
                for block in data_structure:
                    # Skip the default scene
                    if isinstance(block, bpy.types.Scene) and block.name == "Scene":
                        continue
                    # If desired, skip camera
                    if not remove_camera and isinstance(block, (bpy.types.Object, bpy.types.Camera)) \
                            and block.name == "Camera":
                        continue
                    data_structure.remove(block)

    @staticmethod
    def remove_custom_properties():
        """ Remove all custom properties registered at global entities like the scene. """
        for key in list(bpy.context.scene.keys()):
            del bpy.context.scene[key]
