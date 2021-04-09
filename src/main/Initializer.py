import os
import random
from numpy import random as np_random
from sys import platform
import multiprocessing

import bpy

from src.main.Module import Module
from src.main.GlobalStorage import GlobalStorage
from src.utility.CameraUtility import CameraUtility
from src.utility.Config import Config
from src.utility.DefaultConfig import DefaultConfig


class Initializer(Module):
    """ Does some basic initialization of the blender project.

     - Sets background color
     - Configures computing device
     - Creates camera
     - sets the device type to the fastest option possible -> OPTIX > CUDA > OPEN_CL

     If you want deterministic outputs use the environment variable: "BLENDER_PROC_RANDOM_SEED" and set it to
     the desired seed. (random and numpy random are effected by this)

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - horizon_color
          - A list of three elements specifying rgb of the world's horizon/background color. Default: [0.05, 0.05, 0.05].
          - list
        * - global
          - A dictionary of all global set attributes, which are used if a module does not provide a certain key.
            Default: {}.
          - dict
    """

    def __init__(self, config):
        Module.__init__(self, config)

        # setting up the GlobalStorage
        global_config = Config(self.config.get_raw_dict("global", {}))
        GlobalStorage.init_global(global_config)

        # call the init again to make sure all values from the global config where read correctly, too
        self._default_init()

    def run(self):
        # Set language if necessary
        if bpy.context.preferences.view.language != "en_US":
            print("Setting blender language settings to english during this run")
            bpy.context.preferences.view.language = "en_US"

        prefs = bpy.context.preferences.addons['cycles'].preferences
        # Use cycles
        bpy.context.scene.render.engine = 'CYCLES'

        if platform == "darwin":
            # there is no gpu support in mac os so use the cpu with maximum power
            bpy.context.scene.cycles.device = "CPU"
            bpy.context.scene.render.threads = multiprocessing.cpu_count()
        else:
            bpy.context.scene.cycles.device = "GPU"
            preferences = bpy.context.preferences.addons['cycles'].preferences
            for device_type in preferences.get_device_types(bpy.context):
                preferences.get_devices_for_type(device_type[0])
            for gpu_type in ["OPTIX", "CUDA"]:
                found = False
                for device in preferences.devices:
                    if device.type == gpu_type:
                        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = gpu_type
                        print('Device {} of type {} found and used.'.format(device.name, device.type))
                        found = True
                        break
                if found:
                    break
            # make sure that all visible GPUs are used
            for group in prefs.get_devices():
                for d in group:
                    d.use = True

        # setting the frame end, will be changed by the camera loader modules
        bpy.context.scene.frame_end = 0

        # Sets background color
        world = bpy.data.worlds['World']
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[0].default_value[:3] = self.config.get_list("horizon_color", [0.05, 0.05, 0.05])

        # Create the camera
        cam = bpy.data.cameras.new("Camera")
        cam_ob = bpy.data.objects.new("Camera", cam)
        bpy.context.scene.collection.objects.link(cam_ob)
        bpy.context.scene.camera = cam_ob

        # Set default intrinsics
        CameraUtility.set_intrinsics_from_blender_params(DefaultConfig.fov, DefaultConfig.resolution_x, DefaultConfig.resolution_y, DefaultConfig.clip_start, DefaultConfig.clip_end, DefaultConfig.pixel_aspect_x, DefaultConfig.pixel_aspect_y, DefaultConfig.shift_x, DefaultConfig.shift_y, "FOV")
        CameraUtility.set_stereo_parameters(DefaultConfig.stereo_convergence_mode, DefaultConfig.stereo_convergence_distance, DefaultConfig.stereo_interocular_distance)

        random_seed = os.getenv("BLENDER_PROC_RANDOM_SEED")
        if random_seed:
            print("Got random seed: {}".format(random_seed))
            try:
                random_seed = int(random_seed)
            except ValueError as e:
                raise e
            random.seed(random_seed)
            np_random.seed(random_seed)
