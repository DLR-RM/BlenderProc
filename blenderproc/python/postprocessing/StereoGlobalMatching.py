"""Use stereo global matching to calculate an distance image. """

from typing import Tuple, List, Optional

import bpy
import cv2
import numpy as np

from blenderproc.python.camera import CameraUtility


def stereo_global_matching(color_images: List[np.ndarray], depth_max: Optional[float] = None, window_size: int = 7,
                           num_disparities: int = 32, min_disparity: int = 0, disparity_filter: bool = True,
                           depth_completion: bool = True) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """ Does the stereo global matching in the following steps:
    1. Collect camera object and its state,
    2. For each frame, load left and right images and call the `sgm()` methode.
    3. Write the results to a numpy file.

    :param color_images: A list of stereo images, where each entry has the shape [2, height, width, 3].
    :param depth_max: The maximum depth value for clipping the resulting depth values. If None,
                      distance_start + distance_range that were configured for distance rendering are used.
    :param window_size: Semi-global matching kernel size. Should be an odd number.
    :param num_disparities: Semi-global matching number of disparities. Should be > 0 and divisible by 16.
    :param min_disparity: Semi-global matching minimum disparity.
    :param disparity_filter: Applies post-processing of the generated disparity map using WLS filter.
    :param depth_completion: Applies basic depth completion using image processing techniques.
    :return: Returns the computed depth and disparity images for all given frames.
    """
    # Collect camera and camera object
    cam_ob = bpy.context.scene.camera
    cam = cam_ob.data

    baseline = cam.stereo.interocular_distance
    if not baseline:
        raise Exception("Stereo parameters are not set. Make sure to enable RGB stereo rendering before this module.")

    if depth_max is None:
        depth_max = bpy.context.scene.world.mist_settings.start + bpy.context.scene.world.mist_settings.depth

    baseline = cam.stereo.interocular_distance
    if not baseline:
        raise Exception("Stereo parameters are not set. Make sure to enable RGB stereo rendering before this module.")

    focal_length = CameraUtility.get_intrinsics_as_K_matrix()[0, 0]

    depth_frames = []
    disparity_frames = []
    for color_image in color_images:
        depth, disparity = _StereoGlobalMatching.stereo_global_matching(color_image[0], color_image[1], baseline,
                                                                        depth_max, focal_length, window_size,
                                                                        num_disparities, min_disparity,
                                                                        disparity_filter, depth_completion)

        depth_frames.append(depth)
        disparity_frames.append(disparity)

    return depth_frames, disparity_frames


class _StereoGlobalMatching:

    @staticmethod
    def stereo_global_matching(left_color_image: np.ndarray, right_color_image: np.ndarray, baseline: float,
                               depth_max: float, focal_length: float, window_size: int = 7, num_disparities: int = 32,
                               min_disparity: int = 0, disparity_filter: bool = True,
                               depth_completion: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """ Semi global matching funciton, for more details on what this function does check the original paper
        https://elib.dlr.de/73119/1/180Hirschmueller.pdf

        :param left_color_image: The left color image.
        :param right_color_image: The right color image.
        :param baseline: The baseline that was used for rendering the two images.
        :param depth_max: The maximum depth value for clipping the resulting depth values.
        :param focal_length: The focal length that was used for rendering the two images.
        :param window_size: Semi-global matching kernel size. Should be an odd number.
        :param num_disparities: Semi-global matching number of disparities. Should be > 0 and divisible by 16.
        :param min_disparity: Semi-global matching minimum disparity.
        :param disparity_filter: Applies post-processing of the generated disparity map using WLS filter.
        :param depth_completion: Applies basic depth completion using image processing techniques.
        :return: depth, disparity
         """
        if window_size % 2 == 0:
            raise ValueError("Window size must be an odd number")

        if not (num_disparities > 0 and num_disparities % 16 == 0):
            raise ValueError("Number of disparities must be > 0 and divisible by 16")

        left_matcher = cv2.StereoSGBM_create(
            minDisparity=min_disparity,
            numDisparities=num_disparities,
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

        if disparity_filter:
            right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)

            lmbda = 80000
            sigma = 1.2

            wls_filter = cv2.ximgproc.createDisparityWLSFilter(matcher_left=left_matcher)
            wls_filter.setLambda(lmbda)
            wls_filter.setSigmaColor(sigma)

            dispr = right_matcher.compute(right_color_image, left_color_image)

        displ = left_matcher.compute(left_color_image, right_color_image)

        filteredImg = None
        if disparity_filter:
            filteredImg = wls_filter.filter(displ, left_color_image, None, dispr).astype(np.float32)
            filteredImg = cv2.normalize(src=filteredImg, dst=filteredImg, beta=0, alpha=255, norm_type=cv2.NORM_MINMAX)

        disparity_to_be_written = filteredImg if disparity_filter else displ
        disparity = np.float32(np.copy(disparity_to_be_written)) / 16.0

        # Triangulation
        depth = (1.0 / disparity) * baseline * focal_length

        # Clip from depth map to 25 meters
        depth[depth > depth_max] = depth_max
        depth[depth < 0] = 0.0

        if depth_completion:
            depth = _StereoGlobalMatching.fill_in_fast(depth, depth_max)

        return depth, disparity_to_be_written

    @staticmethod
    # https://github.com/kujason/ip_basic/blob/master/ip_basic/depth_map_utils.py
    def fill_in_fast(depth_map: np.ndarray, max_depth: float = 100.0, custom_kernel: Optional[np.ndarray] = None,
                     extrapolate: bool = False, blur_type: str = 'bilateral'):
        """Fast, in-place depth completion.

        :param depth_map: projected depths
        :param max_depth: max depth value for inversion
        :param custom_kernel: kernel to apply initial dilation
        :param extrapolate: whether to extrapolate by extending depths to top of the frame, and applying a 31x31 \
                            full kernel dilation
        :param blur_type: 'bilateral' - preserves local structure (recommended), 'gaussian' - provides lower RMSE
        :return: depth_map: dense depth map
        """

        # Full kernels
        FULL_KERNEL_5 = np.ones((5, 5), np.uint8)
        FULL_KERNEL_7 = np.ones((7, 7), np.uint8)
        FULL_KERNEL_31 = np.ones((31, 31), np.uint8)

        if custom_kernel is None:
            custom_kernel = FULL_KERNEL_5

        # Invert
        valid_pixels = depth_map > 0.1
        depth_map[valid_pixels] = max_depth - depth_map[valid_pixels]

        # Dilate
        depth_map = cv2.dilate(depth_map, custom_kernel)

        # Hole closing
        depth_map = cv2.morphologyEx(depth_map, cv2.MORPH_CLOSE, FULL_KERNEL_5)

        # Fill empty spaces with dilated values
        empty_pixels = depth_map < 0.1
        dilated = cv2.dilate(depth_map, FULL_KERNEL_7)
        depth_map[empty_pixels] = dilated[empty_pixels]

        # Extend the highest pixel to top of image
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
            valid_pixels = depth_map > 0.1
            blurred = cv2.GaussianBlur(depth_map, (5, 5), 0)
            depth_map[valid_pixels] = blurred[valid_pixels]

        # Invert
        valid_pixels = depth_map > 0.1
        depth_map[valid_pixels] = max_depth - depth_map[valid_pixels]

        return depth_map
