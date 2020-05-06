import os
import random
from numpy import random as np_random

import bpy

from src.main.Module import Module
from src.main.GlobalStorage import GlobalStorage
from src.utility.Config import Config

class Initializer(Module):
    """ Does some basic initialization of the blender project.

     - Sets background color
     - Configures computing device
     - Creates camera

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "horizon_color", "A list of three elements specifying rgb of the world's horizon/background color."
       "compute_device_type", "Device to use for computation. Available options are 'CUDA', 'OPTIX', 'OPENCL' and 'NONE'. 'OPTIX' requires a driver version of >=435.12!
    """

    def __init__(self, config):
        Module.__init__(self, config)

        # setting up the GlobalStorage
        global_config = Config(self.config.get_raw_dict("global", {}))
        GlobalStorage.init_global(global_config)

        # call the init again to make sure all values from the global config where read correctly, too
        self._default_init()

    def run(self):
        # Make sure to use the current GPU
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
        print(prefs.compute_device_type, prefs.get_devices())
        for group in prefs.get_devices():
            for d in group:
                d.use = True

        # Set background color
        world = bpy.data.worlds['World']
        world.color[:3] = self.config.get_list("horizon_color", [0.535, 0.633, 0.608])

        # Create the cam
        cam = bpy.data.cameras.new("Camera")
        cam_ob = bpy.data.objects.new("Camera", cam)
        bpy.context.scene.collection.objects.link(cam_ob)
        bpy.context.scene.camera = cam_ob

        # Use cycles
        bpy.context.scene.render.engine = 'CYCLES'

        random_seed = os.getenv("BLENDER_PROC_RANDOM_SEED")
        if random_seed:
            print("Got random seed: {}".format(random_seed))
            try:
                random_seed = int(random_seed)
            except ValueError as e:
                raise e
            random.seed(random_seed)
            np_random.seed(random_seed)
