from src.utility.SetupUtility import SetupUtility
SetupUtility.setup_pip(["scipy"])

from typing import Union, Callable, Any, List, Dict, Tuple

import numpy as np
import bpy

from scipy.ndimage import map_coordinates
from src.main.GlobalStorage import GlobalStorage
from src.utility.CameraUtility import CameraUtility


class LensDistortionUtility:
    """
    This utility class provides to functions to first set up the lens distortion used in this particular BlenderProc
    run and then to apply the said lens distortion parameters to an image rendered by Blender. Both functions must be
    called after each other to use the lens distortion feature correctly. The `set_lens_distortion` fct. has to be
    called before the rendering takes place and the `apply_lens_distortion` has to be applied to the rendered images.

    For more information on lens distortion see: https://en.wikipedia.org/wiki/Distortion_(optics)
    Note that, unlike in that wikipedia entry as of early 2021, we're here using the undistorted-to-distorted formulation.
    """

    @staticmethod
    def set_lens_distortion(k1: float, k2: float, k3: float = 0.0, p1: float = 0.0, p2: float = 0.0):
        """
        This function applies the lens distortion parameters to obtain an distorted-to-undistorted mapping for all
        natural pixels coordinates of the goal distorted image into the real pixel coordinates of the undistorted
        Blender image. Since such a mapping usually yields void image areas, this function suggests a different
        (usually higher) image resolution for the generated Blender image. Eventually, the function
        `apply_lens_distortion` will make us of this image to fill in the goal distorted image with valid color
        values by interpolation. Note that when adapting the internal image resolution demanded from Blender, the
        camera main point (cx,cy) of the K intrinsic matrix is (internally and temporarily) shifted.

        This function has to be used together with the PostProcessing Module, else only the resolution is increased
        but the image(s) will not be distorted.

        This functions stores the "_lens_distortion_is_used" key in the GlobalStorage, which contains the information
        on the mapping and the original image resolution.

        :param k1: First radial distortion parameter as defined by the undistorted-to-distorted Brown-Conrady lens distortion model
        :param k2: Second radial distortion parameter as defined by the undistorted-to-distorted Brown-Conrady lens distortion model
        :param k3: Third radial distortion parameter as defined by the undistorted-to-distorted Brown-Conrady lens distortion model (discouraged)
        :param p1: First decentering distortion parameter as defined by the undistorted-to-distorted Brown-Conrady lens distortion model(discouraged)
        :param p2: Second decentering distortion parameter as defined by the undistorted-to-distorted Brown-Conrady lens distortion model(discouraged)
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

    # P_und are then distorted by the lens, i.e. P_dis = dis(P_und)
    # => Find mapping I_dis(row,column) -> I_und(float,float)
    #
    # We aim at finding the brightness for every discrete pixel of the
    # generated distorted image. In the original undistorted image these
    # are located at real coordinates to be calculated. After that we can
    # interpolate on the original undistorted image.
    # Since dis() cannot be inverted, we iterate (up to ~10 times
    # depending on the AOV and the distortion):
    # 1) assume P_und~=P_dis
    # 2) distort()
    # 3) estimate distance between dist(P_und) and P_dis
    # 4) subtract this distance from the estimated P_und,
    #    perhaps with a factor (>1 for accel, <1 for stability at unstable distortion regions)
    # 5) repeat until P_dis ~ dist(P_und)
    # This works because translations in _dis and _und are approx. equivariant
    # and the mapping is (hopefully) injective (1:1).
    #
    # An alternative, non-iterative approach is P_dis(float,float)=dis(P_und(row,column))
    # and then interpolate on an irregular grid of distorted points. This is faster
    # when generating the mapping matrix but much slower in inference.
    
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

        # Find out the image resolution needed from Blender to generate filled-in distorted images of the desired resolution
        min_und_column_needed = np.sign(np.min(u)) * np.ceil(np.abs(np.min(u)))
        max_und_column_needed = np.sign(np.max(u)) * np.ceil(np.abs(np.max(u)))
        min_und_row_needed = np.sign(np.min(v)) * np.ceil(np.abs(np.min(v)))
        max_und_row_needed = np.sign(np.max(v)) * np.ceil(np.abs(np.max(v)))
        columns_needed = max_und_column_needed - (min_und_column_needed - 1)
        rows_needed = max_und_row_needed - (min_und_row_needed - 1)
        cx_new = cx - (min_und_column_needed - 1)
        cy_new = cy - (min_und_row_needed - 1)
        # To avoid spline boundary approximations at the border pixels ('mode' in map_coordinates() )
        columns_needed += 2
        rows_needed += 2
        cx_new += 1
        cy_new += 1
        # suggested resolution for Blender image generation
        new_image_resolution = np.array([columns_needed, rows_needed])

        # Adapt/shift the mapping function coordinates to the new_image_resolution resolution
        # (if we didn't, the mapping would only be valid for same resolution mapping)
        # (same resolution mapping yields undesired void image areas)
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
        This functions applies the lens distortion mapping that has be precalculated by `set_lens_distortion`.

        Without calling this function the `set_lens_distortion` fct. only increases the image resolution and
        changes the K matrix of the camera.

        :param image: a list of images or an image to be distorted
        :return: a list of images or an image that have been distorted, now in the desired resolution
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
                # Forward mapping in order to distort the undistorted image coordinates
                # and reshape the arrays into the image shape grid.
                # The reference frame for coords is as in DLR CalDe etc. (the upper-left pixel center is at [0,0])
                for i in range(image_distorted.shape[2]):
                    if len(input_image.shape) == 3:
                        image_distorted[:, :, i] = np.reshape(map_coordinates(data[:, :, i], mapping_coords,
                                                                              order=2, mode='nearest'),
                                                              image_distorted[:, :, i].shape)
                    else:
                        image_distorted[:, :, i] = np.reshape(map_coordinates(data, mapping_coords,
                                                                              order=2, mode='nearest'),
                                                              image_distorted[:, :, i].shape)
                # Other options are:
                # - map_coordinates() in all channels at the same time (turns out to be slower)
                # - use torch.nn.functional.grid_sample() instead to do it on the GPU (even in batches)

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
