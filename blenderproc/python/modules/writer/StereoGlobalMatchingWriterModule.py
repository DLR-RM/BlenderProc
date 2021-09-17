from blenderproc.python.postprocessing.StereoGlobalMatching import stereo_global_matching

import os

import bpy
import numpy as np

from blenderproc.python.modules.main.GlobalStorage import GlobalStorage
from blenderproc.python.modules.renderer.RendererInterface import RendererInterface
from blenderproc.python.utility.BlenderUtility import load_image
from blenderproc.python.utility.Utility import Utility


class StereoGlobalMatchingWriterModule(RendererInterface):
    """ Writes depth image generated from the stereo global matching algorithm to file

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - disparity_filter
          - Applies post-processing of the generated disparity map using WLS filter. Default: True
          - bool
        * - depth_completion
          - Applies basic depth completion using image processing techniques. Default: True
          - bool
        * - window_size
          - Semi-global matching kernel size. Should be an odd number. Optional. Default: 7
          - int
        * - num_disparities
          - Semi-global matching number of disparities. Should be > 0 and divisible by 16. Default: 32
          - int
        * - min_disparity
          - Semi-global matching minimum disparity. Optional. Default: 0
          - int
        * - output_disparity
          - Additionally outputs the disparity map. Default: False
          - bool
        * - rgb_output_key
          - The key for the rgb data in the output. Optional. default: colors.
          - string
    """

    def __init__(self, config):
        RendererInterface.__init__(self, config)

        self.rgb_output_key = self.config.get_string("rgb_output_key", "colors")
        if self.rgb_output_key is None:
            raise Exception("RGB output is not registered, please register the RGB renderer before this module.")

    def run(self):
        """ Does the stereo global matching in the following steps:
        1. Collect camera object and its state,
        2. For each frame, load left and right images and call the `sgm()` methode.
        3. Write the results to a numpy file.
        """
        if self._avoid_output:
            print("Avoid output is on, no output produced!")
            return

        if GlobalStorage.is_in_storage("renderer_distance_end"):
            depth_max = GlobalStorage.get("renderer_distance_end")
        else:
            raise RuntimeError("A distance rendering has to be executed before this module is executed, "
                               "else the `renderer_distance_end` is not set!")

        rgb_output_path = Utility.find_registered_output_by_key(self.rgb_output_key)["path"]

        color_images = []
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            path_split = rgb_output_path.split(".")
            path_l = "{}_L.{}".format(path_split[0], path_split[1])
            path_r = "{}_R.{}".format(path_split[0], path_split[1])

            imgL = load_image(path_l % frame)
            imgR = load_image(path_r % frame)
            color_images.append(np.stack((imgL, imgR), 0))

        depth, disparity = stereo_global_matching(
            color_images=color_images,
            depth_max=depth_max,
            window_size=self.config.get_int("window_size", 7),
            num_disparities=self.config.get_int("num_disparities", 32),
            min_disparity=self.config.get_int("min_disparity", 0),
            disparity_filter=self.config.get_bool("disparity_filter", True),
            depth_completion=self.config.get_bool("depth_completion", True)
        )

        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            np.save(os.path.join(self._determine_output_dir(), "stereo-depth_%04d") % frame, depth[frame])

            if self.config.get_bool("output_disparity", False):
                np.save(os.path.join(self._determine_output_dir(), "disparity_%04d") % frame, disparity[frame])

        Utility.register_output(self._determine_output_dir(), "stereo-depth_", "stereo-depth", ".npy", "1.0.0")
        if self.config.get_bool("output_disparity", False):
            Utility.register_output(self._determine_output_dir(), "disparity_", "disparity", ".npy", "1.0.0")
