from typing import Union
import numpy as np
import os
import bpy

import blenderproc.python.camera.CameraUtility as CameraUtility
from blenderproc.python.utility.Utility import Utility


def dist2depth(dist: Union[list, np.ndarray]) -> Union[list, np.ndarray]:
    """
    :param dist: The distance data.
    :return: The depth data
    """

    dist = trim_redundant_channels(dist)

    if isinstance(dist, list) or hasattr(dist, "shape") and len(dist.shape) > 2:
        return [dist2depth(img) for img in dist]
    
    K = CameraUtility.get_intrinsics_as_K_matrix()
    f, cx, cy = K[0,0], K[0,2], K[1,2]
    
    xs, ys = np.meshgrid(np.arange(dist.shape[1]), np.arange(dist.shape[0]))

    # coordinate distances to principal point
    x_opt = np.abs(xs - cx)
    y_opt = np.abs(ys - cy)

    # Solve 3 equations in Wolfram Alpha:
    # Solve[{X == (x-c0)/f0*Z, Y == (y-c1)/f0*Z, X*X + Y*Y + Z*Z = d*d}, {X,Y,Z}]
    depth = dist * f / np.sqrt(x_opt ** 2 + y_opt ** 2 + f ** 2)

    return depth


def depth2dist(depth: Union[list, np.ndarray]) -> Union[list, np.ndarray]:
    """
    :param depth: The depth data.
    :return: The distance data
    """

    depth = trim_redundant_channels(depth)

    if isinstance(depth, list) or hasattr(depth, "shape") and len(depth.shape) > 2:
        return [depth2dist(img) for img in depth]

    K = CameraUtility.get_intrinsics_as_K_matrix()
    f, cx, cy = K[0,0], K[0,2], K[1,2]

    xs, ys = np.meshgrid(np.arange(depth.shape[1]), np.arange(depth.shape[0]))

    # coordinate distances to principal point
    x_opt = np.abs(xs - cx)
    y_opt = np.abs(ys - cy)

    # Solve 3 equations in Wolfram Alpha:
    # Solve[{X == (x-c0)/f0*Z, Y == (y-c1)/f0*Z, X*X + Y*Y + Z*Z = d*d}, {X,Y,Z}]
    dist = depth * np.sqrt(x_opt ** 2 + y_opt ** 2 + f ** 2) / f

    return dist


def remove_segmap_noise(image: Union[list, np.ndarray]) -> Union[list, np.ndarray]:
    """
    A function that takes an image and a few 2D indices, where these indices correspond to pixel values in
    segmentation maps, where these values are not real labels, but some deviations from the real labels, that were
    generated as a result of Blender doing some interpolation, smoothing, or other numerical operations.

    Assumes that noise pixel values won't occur more than 100 times.

    :param image: ndarray of the .exr segmap
    :return: The denoised segmap image
    """

    if isinstance(image, list) or hasattr(image, "shape") and len(image.shape) > 3:
        return [remove_segmap_noise(img) for img in image]

    noise_indices = PostProcessingUtility._determine_noisy_pixels(image)

    for index in noise_indices:
        neighbors = PostProcessingUtility._get_pixel_neighbors(image, index[0], index[
            1])  # Extracting the indices surrounding 3x3 neighbors
        curr_val = image[index[0]][index[1]][0]  # Current value of the noisy pixel

        neighbor_vals = [image[neighbor[0]][neighbor[1]] for neighbor in
                         neighbors]  # Getting the values of the neighbors
        neighbor_vals = np.unique(
            np.array([np.array(index) for index in neighbor_vals]))  # Getting the unique values only

        min = 10000000000
        min_idx = 0

        # Here we iterate through the unique values of the neighbor and find the one closest to the current noisy value
        for idx, n in enumerate(neighbor_vals):
            # Is this closer than the current closest value?
            if n - curr_val <= min:
                # If so, update
                min = n - curr_val
                min_idx = idx

        # Now that we have found the closest value, assign it to the noisy value
        new_val = neighbor_vals[min_idx]
        image[index[0]][index[1]] = np.array([new_val, new_val, new_val])

    return image


def oil_paint_filter(image: Union[list, np.ndarray], filter_size: int = 5, edges_only: bool = True,
                     rgb: bool = False) -> Union[list, np.ndarray]:
    """ Applies the oil paint filter on a single channel image (or more than one channel, where each channel is a replica
        of the other). This could be desired for corrupting rendered depth maps to appear more realistic. Also trims the
        redundant channels if they exist.

        :param image: Input image or list of images
        :param filter_size: Filter size, should be an odd number.
        :param edges_only: If true, applies the filter on the edges only.
        :param rgb: Apply the filter on an RGB image (if the image has 3 channels, they're assumed to not be \
                    replicated).
        :return: filtered image
    """

    import cv2
    from scipy import stats
    if rgb:
        if isinstance(image, list) or hasattr(image, "shape") and len(image.shape) > 3:
            return [oil_paint_filter(img, filter_size, edges_only, rgb) for img in image]

        intensity_img = (np.sum(image, axis=2) / 3.0)

        neighbors = np.array(
            PostProcessingUtility._get_pixel_neighbors_stacked(image, filter_size, return_list=True))
        neighbors_intensity = PostProcessingUtility._get_pixel_neighbors_stacked(intensity_img, filter_size)

        mode_intensity = stats.mode(neighbors_intensity, axis=2)[0].reshape(image.shape[0], image.shape[1])

        # keys here would match all instances of the mode value
        mode_keys = np.argwhere(neighbors_intensity == np.expand_dims(mode_intensity, axis=3))
        # Remove the duplicate keys, since they point to the same value, and to be able to use them for indexing
        _, unique_indices = np.unique(mode_keys[:, 0:2], axis=0, return_index=True)
        unique_keys = mode_keys[unique_indices]

        filtered_img = neighbors[unique_keys[:, 2], unique_keys[:, 0], unique_keys[:, 1], :] \
            .reshape(image.shape[0], image.shape[1], image.shape[2])

        if edges_only:
            edges = cv2.Canny(image, 0, np.max(image))  # Assuming "image" is an uint8 array.
            image[edges > 0] = filtered_img[edges > 0]
            filtered_img = image
    else:
        image = trim_redundant_channels(image)
        if isinstance(image, list) or hasattr(image, "shape") and len(image.shape) > 2:
            return [oil_paint_filter(img, filter_size, edges_only, rgb) for img in image]

        if len(image.shape) == 3 and image.shape[2] > 1:
            image = image[:, :, 0]

        filtered_img = stats.mode(PostProcessingUtility._get_pixel_neighbors_stacked(image, filter_size), axis=2)[0]
        filtered_img = filtered_img.reshape(filtered_img.shape[0], filtered_img.shape[1])

        if edges_only:
            # Handle inf and map input to the range: 0-255
            _image = np.copy(image)
            _max = np.max(_image) if np.max(_image) != np.inf else np.unique(_image)[-2]
            _image[_image > _max] = _max
            _image = (_image / _max) * 255.0

            __img = np.uint8(_image)
            edges = cv2.Canny(__img, 0, np.max(__img))

            image[edges > 0] = filtered_img[edges > 0]
            filtered_img = image

    return filtered_img


def add_gaussian_shifts(image: Union[list, np.ndarray], std: float = 1/2.0) -> Union[list, np.ndarray]:
    """
    Randomly shifts the pixels of the input depth image in x and y direction.

    :param image: Input depth image(s)
    :param std: Standard deviation of pixel shifts, defaults to 1/2.0
    :return: Augmented images
    """
    
    if isinstance(image, list) or hasattr(image, "shape") and len(image.shape) > 2:
        return [add_gaussian_shifts(img, std=std) for img in image]
    
    import cv2

    rows, cols = image.shape 
    gaussian_shifts = np.random.normal(0, std, size=(rows, cols, 2))
    gaussian_shifts = gaussian_shifts.astype(np.float32)

    # creating evenly spaced coordinates  
    xx = np.linspace(0, cols-1, cols)
    yy = np.linspace(0, rows-1, rows)

    # get xpixels and ypixels 
    xp, yp = np.meshgrid(xx, yy)

    xp = xp.astype(np.float32)
    yp = yp.astype(np.float32)

    xp_interp = np.minimum(np.maximum(xp + gaussian_shifts[:, :, 0], 0.0), cols)
    yp_interp = np.minimum(np.maximum(yp + gaussian_shifts[:, :, 1], 0.0), rows)

    depth_interp = cv2.remap(image, xp_interp, yp_interp, cv2.INTER_LINEAR)

    return depth_interp
    

def _filterDisp(disp, dot_pattern_, invalid_disp_):

    size_filt_ = 9

    xx = np.linspace(0, size_filt_-1, size_filt_)
    yy = np.linspace(0, size_filt_-1, size_filt_)

    xf, yf = np.meshgrid(xx, yy)

    xf = xf - int(size_filt_ / 2.0)
    yf = yf - int(size_filt_ / 2.0)

    sqr_radius = (xf**2 + yf**2)
    vals = sqr_radius * 1.2**2 

    vals[vals==0] = 1 
    weights_ = 1 /vals  

    fill_weights = 1 / ( 1 + sqr_radius)
    fill_weights[sqr_radius > 9] = -1.0 

    disp_rows, disp_cols = disp.shape 
    dot_pattern_rows, dot_pattern_cols = dot_pattern_.shape

    lim_rows = np.minimum(disp_rows - size_filt_, dot_pattern_rows - size_filt_)
    lim_cols = np.minimum(disp_cols - size_filt_, dot_pattern_cols - size_filt_)

    center = int(size_filt_ / 2.0)

    window_inlier_distance_ = 0.2

    out_disp = np.ones_like(disp) * invalid_disp_

    interpolation_map = np.zeros_like(disp)

    for r in range(0, lim_rows):

        for c in range(0, lim_cols):

            if dot_pattern_[r+center, c+center] > 0:
                                
                # c and r are the top left corner 
                window  = disp[r:r+size_filt_, c:c+size_filt_] 
                dot_win = dot_pattern_[r:r+size_filt_, c:c+size_filt_] 
  
                valid_dots = dot_win[window < invalid_disp_]

                n_valids = np.sum(valid_dots) / 255.0 
                n_thresh = np.sum(dot_win) / 255.0 

                if n_valids > n_thresh / 1.2: 

                    mean = np.mean(window[window < invalid_disp_])

                    diffs = np.abs(window - mean)
                    diffs = np.multiply(diffs, weights_)

                    cur_valid_dots = np.multiply(np.where(window<invalid_disp_, dot_win, 0), 
                                                 np.where(diffs < window_inlier_distance_, 1, 0))

                    n_valids = np.sum(cur_valid_dots) / 255.0

                    if n_valids > n_thresh / 1.2: 
                    
                        accu = window[center, center] 

                        assert(accu < invalid_disp_)

                        out_disp[r+center, c + center] = round((accu)*8.0) / 8.0

                        interpolation_window = interpolation_map[r:r+size_filt_, c:c+size_filt_]
                        disp_data_window     = out_disp[r:r+size_filt_, c:c+size_filt_]

                        substitutes = np.where(interpolation_window < fill_weights, 1, 0)
                        interpolation_window[substitutes==1] = fill_weights[substitutes ==1 ]

                        disp_data_window[substitutes==1] = out_disp[r+center, c+center]

    return out_disp

def add_kinect_v1_noise(image: Union[list, np.ndarray], baseline_m: float = 0.075, pattern_path: str = 'kinect-pattern_3x3.png', visualize: bool = False) -> Union[list, np.ndarray]:
    """
    Adds Kinect v1 noise to depth images.
    Code adapted from https://github.com/ankurhanda/simkinect 
    Method: Intrinsic Scene Properties from a Single RGB-D Image, CVPR13, Barron et al.

    :param image: depth image(s) in meters
    :param baseline_m: baseline of the sensor in meters
    :param pattern_path: Path to IR pattern from the Kinect V1 or other structured light sensors 
    :param visualize: whether to visualize the depth images
    :return: Noisy depth image(s)
    """
    
    if isinstance(image, list) or hasattr(image, "shape") and len(image.shape) > 2:
        return [add_kinect_v1_noise(img, baseline_m=baseline_m, pattern_path=pattern_path, visualize=visualize) for img in image]
    
    import cv2
    
    if not os.path.exists(pattern_path):
        pattern_path = os.path.join(Utility.get_temporary_directory(), "kinect-pattern_3x3.png")
        if not os.path.exists(pattern_path):
            import urllib.request
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            urllib.request.urlretrieve("https://github.com/ankurhanda/simkinect/blob/master/data/kinect-pattern_3x3.png?raw=true", pattern_path)
            print('Loading kinect pattern 3x3')        
    # reading the image directly in gray with 0 as input 
    dot_pattern_ = cv2.imread(pattern_path, 0)
    
    # tile the original pattern for higher resolution depth images
    tile_size = ((image.shape[0] - 1) // 480 + 1, (image.shape[1] - 1) // 640 + 1)
    dot_pattern_ = np.tile(dot_pattern_, tile_size)

    # various variables to handle the noise modelling
    scale_factor  = 100     # converting depth from m to cm 
    focal_length  = CameraUtility.get_intrinsics_as_K_matrix()[0,0]   # focal length of the camera used 
    invalid_disp_ = 99999999.9

    # Our depth images were scaled by 5000 to store in png format so dividing to get 
    # depth in meters 
    depth = image.astype('float')
    h, w = depth.shape 

    depth_interp = add_gaussian_shifts(depth)

    disp_= focal_length * baseline_m / (depth_interp + 1e-10)
    depth_f = np.round(disp_ * 8.0)/8.0

    out_disp = _filterDisp(depth_f, dot_pattern_, invalid_disp_)

    depth = focal_length * baseline_m / out_disp
    depth[out_disp == invalid_disp_] = 0 

    # The depth here needs to converted to cms so scale factor is introduced 
    # though often this can be tuned from [100, 200] to get the desired banding / quantisation effects 
    noisy_depth = (35130/np.round((35130/np.round(depth*scale_factor)) + np.random.normal(size=(h, w))*(1.0/6.0) + 0.5))/scale_factor 

    if visualize:
        # Displaying side by side the orignal depth map and the noisy depth map with barron noise cvpr 2013 model
        cv2.namedWindow('Adding Kinect Noise', cv2.WINDOW_AUTOSIZE)
        # cv2.imshow('Adding Kinect Noise', np.hstack((depth_uint16, noisy_depth)))
        cv2.imshow('Adding Kinect Noise', np.hstack((image.astype('uint16'), noisy_depth.astype('uint16'))))
        key = cv2.waitKey(0)

        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
        
    return noisy_depth


def trim_redundant_channels(image: Union[list, np.ndarray]) -> Union[list, np.ndarray]:
    """
    Remove redundant channels, this is useful to remove the two of the three channels created for a
    depth or distance image. This also works on a list of images. Be aware that there is no check performed,
    to ensure that all channels are really equal.

    :param image: Input image or list of images
    :return: The trimmed image data.
    """

    if isinstance(image, list) or hasattr(image, "shape") and len(image.shape) > 3:
        return [trim_redundant_channels(ele) for ele in image]

    if hasattr(image, "shape") and len(image.shape) == 3 and image.shape[2] == 3:
        image = image[:, :, 0]  # All channles have the same value, so just extract any single channel

    return image


class PostProcessingUtility:

    @staticmethod
    def _get_pixel_neighbors(data: np.ndarray, i: int, j: int) -> np.ndarray:
        """ Returns the valid neighbor pixel indices of the given pixel.

        :param data: The whole image data.
        :param i: The row index of the pixel
        :param j: The col index of the pixel.
        :return: A list of neighbor point indices.
        """
        neighbors = []
        for p in range(max(0, i - 1), min(data.shape[0], i + 2)):
            for q in range(max(0, j - 1), min(data.shape[1], j + 2)):
                if not (p == i and q == j):  # We don't want the current pixel, just the neighbors
                    neighbors.append([p, q])

        return np.array(neighbors)

    @staticmethod
    def _get_pixel_neighbors_stacked(img: np.ndarray, filter_size: int = 3,
                                     return_list: bool = False) -> Union[list, np.ndarray]:
        """
        Stacks the neighbors of each pixel according to a square filter around each given pixel in the depth dimensions.
        The neighbors are represented by shifting the input image in all directions required to simulate the filter.

        :param img: Input image. Type: blender object of type image.
        :param filter_size: Filter size. Type: int. Default: 5..
        :param return_list: Instead of stacking in the output array, just return a list of the "neighbor" \
                            images along with the input image.
        :return: Either a tensor with the "neighbor" images stacked in a separate additional dimension, or a list of \
                 images of the same shape as the input image, containing the shifted images (simulating the neighbors) \
                 and the input image.
        """
        _min = -int(filter_size / 2)
        _max = _min + filter_size

        rows, cols = img.shape[0], img.shape[1]

        channels = [img]
        for p in range(_min, _max):
            for q in range(_min, _max):
                if p == 0 and q == 0:
                    continue
                shifted = np.zeros_like(img)
                shifted[max(p, 0):min(rows, rows + p), max(q, 0):min(cols, cols + q)] = img[
                                                                                        max(-p, 0):min(rows - p, rows),
                                                                                        max(-q, 0):min(cols - q, cols)]

                channels.append(shifted)

        if return_list:
            return channels
        return np.dstack(tuple(channels))

    @staticmethod
    def _isin(element, test_elements, assume_unique=False, invert=False):
        """ As np.isin is only available after v1.13 and blender is using 1.10.1 we have to implement it manually. """
        element = np.asarray(element)
        return np.in1d(element, test_elements, assume_unique=assume_unique, invert=invert).reshape(element.shape)

    @staticmethod
    def _determine_noisy_pixels(image: np.ndarray) -> np.ndarray:
        """
        :param image: The image data.
        :return: a list of 2D indices that correspond to the noisy pixels. One criteria of finding \
                              these pixels is to use a histogram and find the pixels with frequencies lower than \
                              a threshold, e.g. 100.
        """
        # The map was scaled to be ranging along the entire 16 bit color depth, and this is the scaling down operation
        # that should remove some noise or deviations
        image = ((image * 37) / (65536))  # assuming 16 bit color depth
        image = image.astype(np.int32)
        b, counts = np.unique(image.flatten(), return_counts=True)

        # Removing further noise where there are some stray pixel values with very small counts, by assigning them to
        # their closest (numerically, since this deviation is a
        # result of some numerical operation) neighbor.
        hist = sorted((np.asarray((b, counts)).T), key=lambda x: x[1])
        # Assuming the stray pixels wouldn't have a count of more than 100
        noise_vals = [h[0] for h in hist if h[1] <= 100]
        noise_indices = np.argwhere(PostProcessingUtility._isin(image, noise_vals))

        return noise_indices
