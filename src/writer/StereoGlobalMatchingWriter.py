from src.main.Module import Module
from scipy import stats
from PIL import Image
from math import tan

import os
import bpy
import cv2
import numpy as np
import imageio


def resize(img, new_size, method="nearest"):
    method = method.lower()
    if "lanczos" in method:
        return np.asarray(Image.fromarray(img).resize(new_size, Image.LANCZOS))
    elif "nearest" in method:
        return np.asarray(Image.fromarray(img).resize(new_size, Image.NEAREST))
    else:
        print("UNKNOWN RESIZING METHOD")
        exit(-1)


# Full kernels
FULL_KERNEL_3 = np.ones((3, 3), np.uint8)
FULL_KERNEL_5 = np.ones((5, 5), np.uint8)
FULL_KERNEL_7 = np.ones((7, 7), np.uint8)
FULL_KERNEL_9 = np.ones((9, 9), np.uint8)
FULL_KERNEL_31 = np.ones((31, 31), np.uint8)

# 3x3 cross kernel
CROSS_KERNEL_3 = np.asarray(
    [
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0],
    ], dtype=np.uint8)

# 5x5 cross kernel
CROSS_KERNEL_5 = np.asarray(
    [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
    ], dtype=np.uint8)

# 5x5 diamond kernel
DIAMOND_KERNEL_5 = np.array(
    [
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
        [1, 1, 1, 1, 1],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
    ], dtype=np.uint8)

# 7x7 cross kernel
CROSS_KERNEL_7 = np.asarray(
    [
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
    ], dtype=np.uint8)

# 7x7 diamond kernel
DIAMOND_KERNEL_7 = np.asarray(
    [
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
    ], dtype=np.uint8)


def fill_in_fast(depth_map, max_depth=100.0, custom_kernel=DIAMOND_KERNEL_5,
                 extrapolate=False, blur_type='bilateral'):
    """Fast, in-place depth completion.

    Args:
        depth_map: projected depths
        max_depth: max depth value for inversion
        custom_kernel: kernel to apply initial dilation
        extrapolate: whether to extrapolate by extending depths to top of
            the frame, and applying a 31x31 full kernel dilation
        blur_type:
            'bilateral' - preserves local structure (recommended)
            'gaussian' - provides lower RMSE

    Returns:
        depth_map: dense depth map
    """
    # Invert
    valid_pixels = (depth_map > 0.1)
    depth_map[valid_pixels] = max_depth - depth_map[valid_pixels]

    # Dilate
    depth_map = cv2.dilate(depth_map, custom_kernel)

    # Hole closing
    depth_map = cv2.morphologyEx(depth_map, cv2.MORPH_CLOSE, FULL_KERNEL_5)

    # Fill empty spaces with dilated values
    empty_pixels = (depth_map < 0.1)
    dilated = cv2.dilate(depth_map, FULL_KERNEL_7)
    depth_map[empty_pixels] = dilated[empty_pixels]

    # Extend highest pixel to top of image
    if extrapolate:
        top_row_pixels = np.argmax(depth_map > 0.1, axis=0)
        top_pixel_values = depth_map[top_row_pixels, range(depth_map.shape[1])]

        for pixel_col_idx in range(depth_map.shape[1]):
            depth_map[0:top_row_pixels[pixel_col_idx], pixel_col_idx] = \
                top_pixel_values[pixel_col_idx]

        # Large Fill
        empty_pixels = depth_map < 0.1
        dilated = cv2.dilate(depth_map, FULL_KERNEL_31)
        depth_map[empty_pixels] = dilated[empty_pixels]

    # Median blur
    depth_map = cv2.medianBlur(depth_map, 5)

    # Bilateral or Gaussian blur
    if blur_type == 'bilateral':
        # Bilateral blur
        depth_map = cv2.bilateralFilter(depth_map, 5, 1.5, 2.0)
    elif blur_type == 'gaussian':
        # Gaussian blur
        valid_pixels = (depth_map > 0.1)
        blurred = cv2.GaussianBlur(depth_map, (5, 5), 0)
        depth_map[valid_pixels] = blurred[valid_pixels]

    # Invert
    valid_pixels = (depth_map > 0.1)
    depth_map[valid_pixels] = max_depth - depth_map[valid_pixels]

    return depth_map


class StereoGlobalMatchingWriter(Module):
    """ Writes depth image generated from the stereo global matching algorithm to file

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       "infer_focal_length_from_fov", "If true, then focal length would be calculated from the field of view angle, otherwise the value of the focal length would be read from the config parameter: "focal_length"."
       "disparity_filter", "Applies post-processing of the generated disparity map using WLS filter."
       "depth_completion", "Applies basic depth completion using image processing techniques."
       "focal_length", "Focal length used in the depth calculation step, should be set if 'infer_focal_length_from_fov' is set to false."

       "window_size", "Semi-global matching kernel size. Should be an odd number."
       "num_disparities", "Semi-global matching number of disparities. Should be > 0 and divisible by 16."
       "min_disparity", "Semi-global matching minimum disparity."
    """

    def __init__(self, config):
        Module.__init__(self, config)

        self.rgb_output_key = self.config.get_string("rgb_output_key", "colors")
        if self.rgb_output_key is None:
            raise Exception("RGB output is not registered, please register the RGB renderer before this module.")

        self.output_dir = self._determine_output_dir(False)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def sgm(self, imgL, imgR):
        # wsize default 3; 5; 7 for SGBM reduced size image; 15 for SGBM full size image (1300px and above); 5 Works nicely
        window_size = self.config.get_int("window_size", 7)
        if not (window_size & 1):
            raise Exception("Window size must be an odd number")

        numDisparities = self.config.get_int("num_disparities", 32)
        if not (numDisparities > 0 and numDisparities % 16 == 0):
            raise Exception("Number of disparities must be > 0 and divisible by 16")

        left_matcher = cv2.StereoSGBM_create(
            minDisparity=self.config.get_int("min_disparity", 0),
            numDisparities=numDisparities,
            blockSize=5,
            P1=8 * 3 * window_size ** 2,
            P2=32 * 3 * window_size ** 2,
            disp12MaxDiff=-1,
            uniquenessRatio=15,
            speckleWindowSize=0,
            speckleRange=2,
            preFilterCap=63,
            # mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
            mode=cv2.StereoSGBM_MODE_HH
        )

        if self.config.get_bool("disparity_filter", True):
            right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)

            lmbda = 80000
            sigma = 1.2
            visual_multiplier = 1.0

            wls_filter = cv2.ximgproc.createDisparityWLSFilter(matcher_left=left_matcher)
            wls_filter.setLambda(lmbda)
            wls_filter.setSigmaColor(sigma)

            dispr = right_matcher.compute(imgR, imgL)
            dispr = np.int16(dispr)

        displ = left_matcher.compute(imgL, imgR)
        displ = np.int16(displ)

        filteredImg = None
        if self.config.get_bool("disparity_filter", True):
            filteredImg = wls_filter.filter(displ, imgL, None, dispr).astype(np.float32)
            filteredImg = cv2.normalize(src=filteredImg, dst=filteredImg, beta=0, alpha=255, norm_type=cv2.NORM_MINMAX)

        disparity = np.float64(filteredImg) / 16.0 if self.config.get_bool("disparity_filter", True) else \
            np.float64(displ) / 16.0

        # Crop and resize, due to baseline, a part of the image on the left can't be matched with the one on the right
        disparity = resize(disparity[:, numDisparities:], (self.width, self.height))

        # Triangulation
        depth = (1.0 / disparity) * self.baseline * self.focal_length

        # Clip from depth map to 25 meters
        depth[depth > 25.0] = 25.0
        depth[depth < 0] = 0.0

        if self.config.get_bool("depth_completion", True):
            depth = fill_in_fast(depth, 25.0)

        return depth

    def run(self):
        self.rgb_output_path = self._find_registered_output_by_key(self.rgb_output_key)["path"]

        cam = bpy.context.scene.camera.data

        self.width = bpy.context.scene.render.resolution_x
        self.height = bpy.context.scene.render.resolution_y

        self.baseline = cam.stereo.interocular_distance
        if not self.baseline:
            raise Exception(
                "Stereo parameters are not set. Make sure to enable RGB stereo rendering before this module.")

        if self.config.get_bool("infer_focal_length_from_fov", False):
            fov = cam.angle_x if cam.angle_x else cam.angle
            if not fov:
                raise Exception("Could not obtain field of view angle")
            self.focal_length = float((1.0 / tan(fov / 2.0)) * (float(self.width) / 2.0))
        else:
            self.focal_length = self.config.get_float("focal_length", 0.0)
            if self.focal_length == 0.0:
                raise Exception(
                    "Focal length set to 0. This is either intentional or because no value was set by the user. Either way, this needs to be corrected by setting a value > 0 or enabling 'infer_focal_length_from_fov'.")

        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            path_split = self.rgb_output_path.split(".")
            path_l = "{}_L.{}".format(path_split[0], path_split[1])
            path_r = "{}_R.{}".format(path_split[0], path_split[1])

            imgL = imageio.imread(path_l % frame)
            imgR = imageio.imread(path_r % frame)

            depth = self.sgm(imgL, imgR)

            imageio.imwrite(os.path.join(self.output_dir, "stereo-depth_%04d.exr") % frame, depth)
