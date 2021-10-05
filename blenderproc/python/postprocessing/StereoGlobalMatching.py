from typing import Tuple, List, Optional
import bpy
import cv2
import numpy as np

import blenderproc.python.camera.CameraUtility as CameraUtility
from blenderproc.python.postprocessing.SGMUtility import fill_in_fast
from blenderproc.python.postprocessing.SGMUtility import resize


def stereo_global_matching(color_images: List[np.ndarray], depth_max: Optional[float] = None, window_size: int = 7,
                           num_disparities: int = 32, min_disparity: int = 0, disparity_filter: bool = True,
                           depth_completion: bool = True) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """ Does the stereo global matching in the following steps:
    1. Collect camera object and its state,
    2. For each frame, load left and right images and call the `sgm()` methode.
    3. Write the results to a numpy file.

    :param color_images: A list of stereo images, where each entry has the shape [2, height, width, 3].
    :param depth_max: The maximum depth value for clipping the resulting depth values. If None, distance_start + distance_range that were configured for distance rendering are used.
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
    for frame, color_image in enumerate(color_images):
        depth, disparity = StereoGlobalMatching._sgm(color_image[0], color_image[1], baseline, depth_max, focal_length, window_size, num_disparities, min_disparity, disparity_filter, depth_completion)

        depth_frames.append(depth)
        disparity_frames.append(disparity)

    return depth_frames, disparity_frames

class StereoGlobalMatching:

    @staticmethod
    def _sgm(left_color_image: np.ndarray, right_color_image: np.ndarray, baseline: float, depth_max: float,
             focal_length: float, window_size: int = 7, num_disparities: int = 32, min_disparity: int = 0,
             disparity_filter: bool = True, depth_completion: bool = True) -> Tuple[np.ndarray, np.ndarray]:
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
            raise Exception("Window size must be an odd number")

        if not (num_disparities > 0 and num_disparities % 16 == 0):
            raise Exception("Number of disparities must be > 0 and divisible by 16")

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
        disparity = np.float64(np.copy(disparity_to_be_written)) / 16.0

        # Crop and resize, due to baseline, a part of the image on the left can't be matched with the one on the right
        disparity = resize(disparity[:, num_disparities:], (left_color_image.shape[1], left_color_image.shape[0]))

        # Triangulation
        depth = (1.0 / disparity) * baseline * focal_length

        # Clip from depth map to 25 meters
        depth[depth > depth_max] = depth_max
        depth[depth < 0] = 0.0

        if depth_completion:
            depth = fill_in_fast(depth, depth_max)

        return depth, disparity_to_be_written

