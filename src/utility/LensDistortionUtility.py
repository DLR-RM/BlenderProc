from src.utility.SetupUtility import SetupUtility
SetupUtility.setup_pip(["scipy"])

from typing import Union, Callable, Any, List, Dict, Tuple

import numpy as np
import bpy

from scipy.ndimage import map_coordinates
from src.main.GlobalStorage import GlobalStorage
from src.utility.CameraUtility import CameraUtility


class LensDistortionUtility:

    @staticmethod
    def set_lens_distortion(k1: float, k2: float, k3: float = 0.0, p1: float = 0.0, p2: float = 0.0):
        """
        TODO MISSING
        :param k1:
        :param k2:
        :param k3:
        :param p1:
        :param p2:
        :return:
        """
        if all(v == 0.0 for v in [k1, k2, k3, p1, p2]):
            raise Exception("All given lens distortion parameters (k1, k2, k3, p1, p2) are zero.")

        # save the original image resolution
        original_image_resolution = (bpy.context.scene.render.resolution_y, bpy.context.scene.render.resolution_x)
        # first we need to get the current K matrix
        camera_K_matrix = CameraUtility.get_intrinsics_as_K_matrix()
        fx, fy = camera_K_matrix[0][0], camera_K_matrix[1][1]
        cx, cy = camera_K_matrix[0][2], camera_K_matrix[1][2]

        # get the current desired resolution
        # TODO check how the pixel aspect has to be factored in!
        desired_dis_res = (bpy.context.scene.render.resolution_y, bpy.context.scene.render.resolution_x)
        # Get row,column image coordinates for all pixels for row-wise image flattening
        # The center of the upper-left pixel has coordinates [0,0] both in DLR CalDe and python/scipy
        row = np.repeat(np.arange(0, desired_dis_res[0]), desired_dis_res[1])
        column = np.tile(np.arange(0, desired_dis_res[1]), desired_dis_res[0])

        # P_und is the undistorted pinhole projection at z==1 of all image pixels
        P_und = np.linalg.inv(camera_K_matrix) @ np.vstack((column, row, np.ones(np.prod(desired_dis_res[:2]))))

        # Init dist at undist
        x = P_und[0, :]
        y = P_und[1, :]
        res = [1e3]
        it = 0
        factor = 1.0
        while res[-1] > 0.2:
            r2 = np.square(x) + np.square(y)
            radial_part = (1 + k1 * r2 + k2 * r2 * r2 + k3 * r2 * r2 * r2)
            x_ = x * radial_part + 2 * p2 * x * y + p1 * (r2 + 2 * np.square(x))
            y_ = y * radial_part + 2 * p1 * x * y + p2 * (r2 + 2 * np.square(y))

            error = np.max(np.hypot(fx * (x_ - P_und[0, :]), fy * (y_ - P_und[1, :])))
            res.append(error)
            it += 1

            # Take action if the optimization stalls or gets unstable
            # (distortion models are tricky if badly parameterized, especially in outer regions)
            if (it > 1) and (res[-1] > res[-2] * .999):
                factor *= .5
                if it > 1e3:
                    raise Exception(
                        "The iterative distortion algorithm is unstable/stalled after 1000 iterations. STOP.")
                if error > 1e9:
                    raise Exception("The iterative distortion algorithm is unstable. STOP.")

            # update undistorted projection
            x = x - (x_ - P_und[0, :]) * factor
            y = y - (y_ - P_und[1, :]) * factor

        # u and v are now the pixel coordinates on the undistorted image that
        # will distort into the row,column coordinates of the distorted image
        u = (fx * x + cx)
        v = (fy * y + cy)

        # Stacking this way for the interpolation in the undistorted image array
        mapping_coords = np.vstack([v, u])

        # Find out the resolution needed at the original image to generate filled-in distorted images
        min_und_column_needed = np.sign(np.min(u)) * np.ceil(np.abs(np.min(u)))
        max_und_column_needed = np.sign(np.max(u)) * np.ceil(np.abs(np.max(u)))
        min_und_row_needed = np.sign(np.min(v)) * np.ceil(np.abs(np.min(v)))
        max_und_row_needed = np.sign(np.max(v)) * np.ceil(np.abs(np.max(v)))
        columns_needed = max_und_column_needed - (min_und_column_needed - 1)
        rows_needed = max_und_row_needed - (min_und_row_needed - 1)
        cx_new = cx - (min_und_column_needed - 1) + 1
        cy_new = cy - (min_und_row_needed - 1) + 1
        # newly suggested resolution
        new_image_resolution = np.array([columns_needed, rows_needed])
        # To avoid spline boundary approximations at the border pixels ('mode' in map_coordinates() )
        new_image_resolution += 2

        # Adapt/shift the mapping function coordinates to the new_image_resolution resolution
        # (if we didn't, the mapping would only be valid for same resolution mapping)
        # (same resolution mapping yields undesired void image areas)
        # (this can in theory be performed in init_distortion() if we're positive about the resolution used)
        mapping_coords[0, :] += cy_new - cy
        mapping_coords[1, :] += cx_new - cx

        camera_changed_K_matrix = CameraUtility.get_intrinsics_as_K_matrix()
        # update cx and cy in the K matrix
        camera_changed_K_matrix[0, 2] = cx_new
        camera_changed_K_matrix[1, 2] = cy_new

        # reuse the values, which have been set before
        clip_start = bpy.context.scene.camera.data.clip_start
        clip_end = bpy.context.scene.camera.data.clip_end

        CameraUtility.set_intrinsics_from_K_matrix(camera_changed_K_matrix, new_image_resolution[0],
                                                   new_image_resolution[1], clip_start, clip_end)
        GlobalStorage.set("_lens_distortion_is_used", {"mapping_coords": mapping_coords,
                                                       "original_image_res": original_image_resolution})

    @staticmethod
    def apply_lens_distortion(image: Union[List[np.ndarray], np.ndarray]) -> Union[List[np.ndarray], np.ndarray]:
        """
        TODO

        :param image: a list of images or an image, which will be distorted
        :return: a list of images or an image which have been distorted
        """
        # if lens distortion was used apply it now
        if GlobalStorage.is_in_storage("_lens_distortion_is_used"):
            # extract the necessary params from the GlobalStorage
            content = GlobalStorage.get("_lens_distortion_is_used")
            mapping_coords = content["mapping_coords"]
            original_image_res = content["original_image_res"]

            def _internal_apply(input_image: np.ndarray) -> np.ndarray:
                """
                Applies the distortion to the input image
                :param input_image: input image, which will be distorted
                :return: distorted input image
                """
                amount_of_output_channels = 1
                if len(input_image.shape) == 3:
                    amount_of_output_channels = input_image.shape[2]
                image_distorted = np.zeros((original_image_res[0], original_image_res[1], amount_of_output_channels))
                used_dtpye = input_image.dtype
                data = input_image.astype(np.float)
                for i in range(image_distorted.shape[2]):
                    # TODO check the order and the mode, for non rgb data?
                    # The reference frame for coords is here as in DLR CalDe (the upper-left pixel center is at [0,0])
                    if len(input_image.shape) == 3:
                        image_distorted[:, :, i] = np.reshape(map_coordinates(data[:, :, i], mapping_coords,
                                                                              order=2, mode='nearest'),
                                                              image_distorted[:, :, i].shape)
                    else:
                        image_distorted[:, :, i] = np.reshape(map_coordinates(data, mapping_coords,
                                                                              order=2, mode='nearest'),
                                                              image_distorted[:, :, i].shape)

                if used_dtpye == np.uint8:
                    image_distorted = np.clip(image_distorted, 0, 255)
                data = image_distorted.astype(used_dtpye)
                if len(input_image.shape) == 2:
                    return data[:, :, 0]
                else:
                    return data

            if isinstance(image, list):
                return [_internal_apply(img) for img in image]
            elif isinstance(image, np.ndarray):
                return _internal_apply(image)
            else:
                raise Exception(f"This type can not be worked with here: {type(image)}, only "
                                f"np.ndarray or list of np.ndarray are supported")
        else:
            raise Exception("Applying of a lens distortion is only possible if prior to calling this method "
                            "CameraUtility.set_lens_distortion(...) was called, this could have been done via the"
                            "CameraInterface module, see lens_distortion.")
