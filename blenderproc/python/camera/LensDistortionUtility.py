import os
from typing import Union, Callable, Any, List, Dict, Tuple, Optional

import numpy as np
import yaml
import bpy
from scipy.ndimage import map_coordinates

from blenderproc.python.modules.main.GlobalStorage import GlobalStorage
import blenderproc.python.camera.CameraUtility as CameraUtility
from blenderproc.python.utility.MathUtility import change_source_coordinate_frame_of_transformation_matrix


"""
This file provides to functions to first set up the lens distortion used in this particular BlenderProc
run and then to apply the said lens distortion parameters to an image rendered by Blender. Both functions must be
called after each other to use the lens distortion feature correctly. The `set_lens_distortion` fct. has to be
called before the rendering takes place and the `apply_lens_distortion` has to be applied to the rendered images.

For more information on lens distortion see: https://en.wikipedia.org/wiki/Distortion_(optics)
Note that, unlike in that wikipedia entry as of early 2021, we're here using the undistorted-to-distorted formulation.
"""

def set_lens_distortion(k1: float, k2: float, k3: float = 0.0, p1: float = 0.0, p2: float = 0.0, use_global_storage: bool = False) -> np.ndarray:
    """
    This function applies the lens distortion parameters to obtain an distorted-to-undistorted mapping for all
    natural pixels coordinates of the goal distorted image into the real pixel coordinates of the undistorted
    Blender image. Since such a mapping usually yields void image areas, this function suggests a different
    (usually higher) image resolution for the generated Blender image. Eventually, the function
    `apply_lens_distortion` will make us of this image to fill in the goal distorted image with valid color
    values by interpolation. Note that when adapting the internal image resolution demanded from Blender, the
    camera main point (cx,cy) of the K intrinsic matrix is (internally and temporarily) shifted.

    This function has to be used together with bproc.postprocessing.apply_lens_distortion(), else only the 
    resolution is increased but the image(s) will not be distorted.

    :param k1: First radial distortion parameter (of 3rd degree in radial distance) as defined
            by the undistorted-to-distorted Brown-Conrady lens distortion model, which is conform to
            the current DLR CalLab/OpenCV/Bouguet/Kalibr implementations.
            Note that undistorted-to-distorted means that the distortion parameters are multiplied
            by undistorted, normalized camera projections to yield distorted projections, that are in
            turn digitized by the intrinsic camera matrix.
    :param k2: Second radial distortion parameter (of 5th degree in radial distance) as defined
            by the undistorted-to-distorted Brown-Conrady lens distortion model, which is conform
            to the current DLR CalLab/OpenCV/Bouguet/Kalibr implementations.
    :param k3: Third radial distortion parameter (of 7th degree in radial distance) as defined
            by the undistorted-to-distorted Brown-Conrady lens distortion model, which is conform to
            the current DLR CalLab/OpenCV/Bouguet/Kalibr implementations.
            The use of this parameter is discouraged unless the angular field of view is too high,
            rendering it necessary, and the parameter allows for a distorted projection in the whole
            sensor size (which isn't always given by features-driven camera calibration).
    :param p1: First decentering distortion parameter as defined by the undistorted-to-distorted
            Brown-Conrady lens distortion model in (Brown, 1965; Brown, 1971; Weng et al., 1992) and is
            comform to the current DLR CalLab implementation. Note that OpenCV/Bouguet/Kalibr permute them.
            This parameter shares one degree of freedom (j1) with p2; as a consequence, either both
            parameters are given or none. The use of these parameters is discouraged since either current
            cameras do not need them or their potential accuracy gain is negligible w.r.t. image processing.
    :param p2: Second decentering distortion parameter as defined by the undistorted-to-distorted
            Brown-Conrady lens distortion model in (Brown, 1965; Brown, 1971; Weng et al., 1992) and is
            comform to the current DLR CalLab implementation. Note that OpenCV/Bouguet/Kalibr permute them.
            This parameter shares one degree of freedom (j1) with p1; as a consequence, either both
            parameters are given or none. The use of these parameters is discouraged since either current
            cameras do not need them or their potential accuracy gain is negligible w.r.t. image processing.
    :use_global_storage: Whether to save the mapping coordinates and original image resolution in a global storage (backward compat for configs)
    :return: mapping coordinates from distorted to undistorted image pixels
    """
    if all(v == 0.0 for v in [k1, k2, k3, p1, p2]):
        raise Exception("All given lens distortion parameters (k1, k2, k3, p1, p2) are zero.")

    # save the original image resolution (desired output resolution)
    original_image_resolution = (bpy.context.scene.render.resolution_y, bpy.context.scene.render.resolution_x)

    # get the current K matrix (skew==0 in Blender)
    camera_K_matrix = CameraUtility.get_intrinsics_as_K_matrix()
    fx, fy = camera_K_matrix[0][0], camera_K_matrix[1][1]
    cx, cy = camera_K_matrix[0][2], camera_K_matrix[1][2]

    # Get row,column image coordinates for all pixels for row-wise image flattening
    # The center of the upper-left pixel has coordinates [0,0] both in DLR CalDe and python/scipy
    row = np.repeat(np.arange(0, original_image_resolution[0]), original_image_resolution[1])
    column = np.tile(np.arange(0, original_image_resolution[1]), original_image_resolution[0])

    # P_und is the undistorted pinhole projection at z==1 of all image pixels
    P_und = np.linalg.inv(camera_K_matrix) @ np.vstack((column, row, np.ones(np.prod(original_image_resolution[:2]))))

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
    while res[-1] > 0.15:
        r2 = np.square(x) + np.square(y)
        radial_part = (1 + k1 * r2 + k2 * r2 * r2 + k3 * r2 * r2 * r2)
        x_ = x * radial_part + 2 * p2 * x * y + p1 * (r2 + 2 * np.square(x))
        y_ = y * radial_part + 2 * p1 * x * y + p2 * (r2 + 2 * np.square(y))

        error = np.max(np.hypot(fx * (x_ - P_und[0, :]), fy * (y_ - P_und[1, :])))
        res.append(error)
        it += 1

        # Take action if the optimization stalls or gets unstable
        # (distortion models are tricky if badly parameterized, especially in outer regions)
        if (it > 1) and (res[-1] > res[-2] * .99999):
            print("The residual for the worst distorted pixel got unstable/stalled.")
            # factor *= .5
            if it > 1e3:
                raise Exception(
                    "The iterative distortion algorithm is unstable/stalled after 1000 iterations.")
            if error > 1e9:
                print("Some (corner) pixels of the desired image are not defined by the used lens distortion model.")
                print("We invite you to double-check your distortion model.")
                print("The parameters k3,p1,p2 can easily overshoot for regions where the calibration software had no datapoints.")
                print("You can either:")
                print("- take more projections (ideally image-filling) at the image corners and repeat calibration,")
                print("- reduce the # of released parameters to calibrate to k1,k2, or")
                print("- reduce the target image size (subtract some lines and columns from the desired resolution")
                print("  and subtract at most that number of lines and columns from the main point location).")
                print("BlenderProc will not generate incomplete images with void regions since these are not useful for ML (data leakage).")
                print("For that, you can use the Matlab code in robotic.de/callab, which robustifies against these unstable pixels.")
                raise Exception("The iterative distortion algorithm is unstable.")

        # update undistorted projection
        x = x - (x_ - P_und[0, :])  # * factor
        y = y - (y_ - P_und[1, :])  # * factor

    # u and v are now the pixel coordinates on the undistorted image that
    # will distort into the row,column coordinates of the distorted image
    u = (fx * x + cx)
    v = (fy * y + cy)

    # Stacking this way for the interpolation in the undistorted image array
    mapping_coords = np.vstack([v, u])

    # Find out the image resolution needed from Blender to generate filled-in distorted images of the desired resolution
    min_und_column_needed = np.floor(np.min(u))
    max_und_column_needed = np.ceil(np.max(u))
    min_und_row_needed = np.floor(np.min(v))
    max_und_row_needed = np.ceil(np.max(v))
    columns_needed = max_und_column_needed + 1 - min_und_column_needed
    rows_needed = max_und_row_needed + 1 - min_und_row_needed
    cx_new = cx - min_und_column_needed
    cy_new = cy - min_und_row_needed
    # To avoid spline boundary approximations at the border pixels ('mode' in map_coordinates() )
    columns_needed += 2
    rows_needed += 2
    cx_new += 1
    cy_new += 1
    # suggested resolution for Blender image generation
    new_image_resolution = np.array([columns_needed, rows_needed], dtype=int)

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

    if use_global_storage:
        GlobalStorage.set("_lens_distortion_is_used", {"mapping_coords": mapping_coords,
                                                    "original_image_res": original_image_resolution})
    return mapping_coords


def apply_lens_distortion(image: Union[List[np.ndarray], np.ndarray],
                          mapping_coords: Optional[np.ndarray] = None,
                          orig_res_x: Optional[int] = None,
                          orig_res_y: Optional[int] = None,
                          use_interpolation: bool = True) -> Union[List[np.ndarray], np.ndarray]:
    """
    This functions applies the lens distortion mapping that needs to be precalculated by `bproc.camera.set_lens_distortion()`.

    Without calling this function the `set_lens_distortion` fct. only increases the image resolution and
    changes the K matrix of the camera.

    :param image: a list of images or an image to be distorted
    :param mapping_coords: an array of pixel mappings from undistorted to distorted image
    :param orig_res_x: original and output width resolution of the image
    :param orig_res_y: original and output height resolution of the image
    :param use_interpolation: if this is True, for each pixel an interpolation will be performed, if this is false the nearest pixel will be used
    :return: a list of images or an image that have been distorted, now in the desired (original) resolution
    """

    if mapping_coords is None or orig_res_x is None or orig_res_y is None: 
        # if lens distortion was used apply it now
        if GlobalStorage.is_in_storage("_lens_distortion_is_used"):
            # extract the necessary params from the GlobalStorage
            content = GlobalStorage.get("_lens_distortion_is_used")
            mapping_coords = content["mapping_coords"]
            orig_res_y, orig_res_x = content["original_image_res"]
        else:
            raise Exception("Applying of a lens distortion is only possible after calling "
                            "bproc.camera.set_lens_distortion(...) and pass 'mapping_coords' and "
                            "'orig_res_x' + 'orig_res_x' to bproc.postprocessing.apply_lens_distortion(...). "
                            "Previously this could also have been done via the CameraInterface module, "
                            "see the example on lens_distortion.")
    interpolation_order = 2 if use_interpolation else 0

    def _internal_apply(input_image: np.ndarray) -> np.ndarray:
        """
        Applies the distortion to the input image
        :param input_image: input image, which will be distorted
        :return: distorted input image
        """
        amount_of_output_channels = 1
        if len(input_image.shape) == 3:
            amount_of_output_channels = input_image.shape[2]
        image_distorted = np.zeros((orig_res_y, orig_res_x, amount_of_output_channels))
        used_dtpye = input_image.dtype
        data = input_image.astype(np.float)
        # Forward mapping in order to distort the undistorted image coordinates
        # and reshape the arrays into the image shape grid.
        # The reference frame for coords is as in DLR CalDe etc. (the upper-left pixel center is at [0,0])
        for i in range(image_distorted.shape[2]):
            if len(input_image.shape) == 3:
                image_distorted[:, :, i] = np.reshape(map_coordinates(data[:, :, i], mapping_coords,
                                                                      order=interpolation_order,
                                                                      mode='nearest'), image_distorted[:, :, i].shape)
            else:
                image_distorted[:, :, i] = np.reshape(map_coordinates(data, mapping_coords, order=interpolation_order,
                                                                      mode='nearest'),
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


def set_camera_parameters_from_config_file(camera_intrinsics_file_path: str, read_the_extrinsics: bool = False,
                                           camera_index: int = 0) -> Tuple[int, int, np.ndarray]:
    """
    This function sets the camera intrinsic parameters based on a config file, currently it only supports the
    DLR-RMC camera calibration file format used in the "DLR CalDe and DLR CalLab" camera calibration toolbox.
    The calibration file allows to use multiple cameras, but only one can be used inside of BlenderProc per run.

    :param camera_intrinsics_file_path: Path to the calibration file
    :param camera_index: Used camera index
    :return: mapping coordinates from distorted to undistorted image pixels, as returned from set_lens_distortion()
    """
    if not os.path.exists(camera_intrinsics_file_path):
        raise Exception("The camera intrinsics file does not exist: {}".format(camera_intrinsics_file_path))

    def _is_number(value: str) -> bool:
        # check if the given string value is a digit (float or int)
        if value.isnumeric():
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    with open(camera_intrinsics_file_path, "r") as file:
        final_lines = []
        for line in file.readlines():
            line = line.strip()
            if "#" in line:
                line = line[:line.find("#")].strip()
            if "[" in line and "]" in line:
                # add commas in between the numbers, which are seperated by spaces
                line = line.replace(";", " ; ")
                line = line.replace("[", "[ ")
                line = line.replace("]", " ]")
                for i in range(15):
                    line = line.replace("  ", " ")
                elements = line.split(" ")
                if elements:
                    final_elements = []
                    # add in commas between two elements if the current and the next element are numbers
                    for i in range(len(elements) - 1):
                        final_elements.append(elements[i])
                        if _is_number(elements[i]) and _is_number(elements[i + 1]):
                            final_elements.append(",")
                    final_elements.append(elements[-1])
                    line = " ".join(final_elements)
            if ";" in line and "[" in line and "]" in line:
                # this line contains a matrix
                line = line.replace("[", "[[").replace("]", "]]").replace(";", "], [")
            # convert it to yaml format
            if line.startswith("camera."):
                current_nr = line[len("camera."):line.find(".", len("camera."))]
                if _is_number(current_nr):
                    # remove all lines which are not focused around the selected camera index
                    if int(current_nr) != camera_index:
                        line = ""
                else:
                    # remove lines which are not specified to a certain camera
                    line = ""
            line = line.replace(f"camera.{camera_index}.", "")
            if line.count("=") == 1:
                line = f'"{line.split("=")[0]}"= {line.split("=")[1]}'
            else:
                line = ""
            line = line.replace("=", ":")
            if line:
                final_lines.append(line)

    extracted_camera_parameters = yaml.safe_load("\n".join(final_lines))
    print(f"Interpreted intrinsics from DLR-RMC camera calibration file: {extracted_camera_parameters}")
    # check version and origin parameters
    if extracted_camera_parameters.get("version") is None or extracted_camera_parameters["version"] != 2:
        if extracted_camera_parameters.get("version") is None:
            raise Exception("The version tag is not set in the DLR-RMC camera calibration file!")
        else:
            raise Exception("Only version 2 is supported for the DLR-RMC camera calibration file, not {}".format(extracted_camera_parameters["version"]))
    if extracted_camera_parameters.get("origin") is None or extracted_camera_parameters["origin"] != "center":
        raise Exception("The origin in the DLR-RMC camera calibration file has to be defined and set to center for BlenderProc distortion to work.")
    # set intrinsics based on the yaml-read matrix called A and the yaml-read camera image size
    CameraUtility.set_intrinsics_from_K_matrix(extracted_camera_parameters.get("A"), extracted_camera_parameters["width"],
                                               extracted_camera_parameters["height"])
    # setup the lens distortion and adapt intrinsics so that it can be later used in the PostProcessing
    mapping_coords = set_lens_distortion(extracted_camera_parameters["k1"], extracted_camera_parameters.get("k2", 0.0),
                                         extracted_camera_parameters.get("k3", 0.0), extracted_camera_parameters.get("p1", 0.0),
                                         extracted_camera_parameters.get("p2", 0.0))
    if read_the_extrinsics:
        cam2world = np.eye(4)
        cam2world[:3, :3] = np.array(extracted_camera_parameters["R"])
        cam2world[:3, 3] = np.array(extracted_camera_parameters["T"])
        cam2world = change_source_coordinate_frame_of_transformation_matrix(cam2world, ["X", "-Y", "-Z"])
        CameraUtility.add_camera_pose(cam2world)
    return extracted_camera_parameters["width"], extracted_camera_parameters["height"], mapping_coords
