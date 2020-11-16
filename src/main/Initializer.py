import os
import random
from numpy import random as np_random
from sys import platform
import multiprocessing

import bpy

from src.main.Module import Module
from src.main.GlobalStorage import GlobalStorage
from src.utility.Config import Config
from src.utility.CameraUtility import CameraUtility

class Initializer(Module):
    """ Does some basic initialization of the blender project.

     - Sets background color
     - Configures computing device
     - Creates camera
     - sets the device type to the fastest option possible -> OPTIX > CUDA > OPEN_CL

     If you want deterministic outputs use the environment variable: "BLENDER_PROC_RANDOM_SEED" and set it to
     the desired seed. (random and numpy random are effected by this)

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "horizon_color", "A list of three elements specifying rgb of the world's horizon/background color."
                        "Type: list. Default: [0.535, 0.633, 0.608]."
       "global", "A dictionary of all global set attributes, which are used if a module does not provide a certain "
                 "key. Type: dict. Default: {}."
       "intrinsics", "A dictionary containing camera intrinsic parameters. If not given, the intrinsic parameters are not changed. See the last table for available parameters. Type: dict. Default: {}."


    **Intrinsic camera parameters**:

    .. csv-table::
        :header: "Keyword", "Description"

        "cam_K", "Camera Matrix K. Cx, cy are defined in a coordinate system with (0,0) being the CENTER of the top-left "
                 "pixel - this is the convention e.g. used in OpenCV. Type: list. Default: []."
        "shift", "Principal Point deviation from center. The unit is proportion of the larger image dimension. Type: float."
        "fov", "The FOV (normally the angle between both sides of the frustum, if fov_is_half is True than its assumed "
               "to be the angle between forward vector and one side of the frustum). Type: float. Default: 0.691111."
        "resolution_x", "Width resolution of the camera. Type: int. Default: 512. "
        "resolution_y", "Height resolution of the camera. Type: int. Default: 512. "
        "pixel_aspect_x", "Pixel aspect ratio x. Type: float. Default: 1."
        "pixel_aspect_y", "Pixel aspect ratio y. Type: float. Default: 1."
        "clip_start", "Near clipping. Type: float. Default: 0.1."
        "clip_end", "Far clipping. Type: float. Default: 1000."
        "stereo_convergence_mode", "How the two cameras converge (e.g. Off-Axis where both cameras are shifted inwards "
                                   "to converge in the convergence plane, or parallel where they do not converge and "
                                   "are parallel). Type: string. Default: "OFFAXIS"."
        "convergence_distance", "The convergence point for the stereo cameras (i.e. distance from the projector to the "
                                "projection screen). Type: float. Default: 1.95."
        "interocular_distance", "Distance between the camera pair. Type: float. Default: 0.065.",

    """

    def __init__(self, config):
        Module.__init__(self, config)

        # setting up the GlobalStorage
        global_config = Config(self.config.get_raw_dict("global", {}))
        GlobalStorage.init_global(global_config)

        # call the init again to make sure all values from the global config where read correctly, too
        self._default_init()


    def _set_cam_intrinsics(self, cam, config):
        """ Sets camera intrinsics

        :param cam: The camera which contains only camera specific attributes.
        :param config: A configuration object with cam intrinsics.
        """
        width, height = config.get_int("resolution_x", 512), config.get_int("resolution_y", 512)

        # Clipping (Default values are the same as default blender values)
        clip_start = config.get_float("clip_start", 0.1)
        clip_end = config.get_float("clip_end", 1000)

        # Convert intrinsics from loader/config to Blender format
        cam.lens_unit = 'FOV'
        if config.has_param("cam_K"):
            if config.has_param("fov"):
                print('WARNING: FOV defined in config is ignored. Mutually exclusive with cam_K')
            if config.has_param("pixel_aspect_x"):
                print('WARNING: pixel_aspect_x defined in config is ignored. Mutually exclusive with cam_K')

            cam_K = np.array(config.get_list("cam_K")).reshape(3, 3).astype(np.float32)

            CameraUtility.set_intrinsics_from_K_matrix(cam_K, width, height, clip_start, clip_end)
        else:
            # Set FOV (Default value is the same as the default blender value)
            fov = config.get_float("fov", 0.691111)

            # Set Pixel Aspect Ratio
            pixel_aspect_x = config.get_float("pixel_aspect_x", 1.)
            pixel_aspect_y = config.get_float("pixel_aspect_y", 1.)

            CameraUtility.set_intrinsics_from_blender_params(fov, width, height, clip_start, clip_end, pixel_aspect_x, pixel_aspect_y, 0, 0, lens_unit="FOV")

            if bpy.context.scene.render.pixel_aspect_x != 1:
                print('WARNING: Using non-square pixel aspect ratio. Can influence intrinsics.')

        CameraUtility.set_stereo_parameters(config.get_string("stereo_convergence_mode", "OFFAXIS"), config.get_float("convergence_distance", 1.95), config.get_float("interocular_distance", 0.065))

    def run(self):
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
        world.color[:3] = self.config.get_list("horizon_color", [0.535, 0.633, 0.608])

        # Create the camera
        cam = bpy.data.cameras.new("Camera")
        cam_ob = bpy.data.objects.new("Camera", cam)
        bpy.context.scene.collection.objects.link(cam_ob)
        bpy.context.scene.camera = cam_ob
        # Set default intrinsics
        self._set_cam_intrinsics(cam, Config(self.config.get_raw_dict("camera_intrinsics", {})))

        random_seed = os.getenv("BLENDER_PROC_RANDOM_SEED")
        if random_seed:
            print("Got random seed: {}".format(random_seed))
            try:
                random_seed = int(random_seed)
            except ValueError as e:
                raise e
            random.seed(random_seed)
            np_random.seed(random_seed)
