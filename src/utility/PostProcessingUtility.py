import os
import numpy as np
import csv

import bpy

from src.utility.BlenderUtility import load_image

class PostProcessingUtility:  
        
    @staticmethod
    def dist2depth(dist):
        """
        :param dist: The distance data.
        :return: The depth data
        """
        if len(dist.shape) > 2:
            dist = dist[:, :, 0] # All channles have the same value, so just extract any single channel
        else:
            dist = dist.squeeze()
        
        height, width = dist.shape

        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        max_resolution = max(width, height) 

        # Compute Intrinsics from Blender attributes (can change)
        f = width / (2 * np.tan(cam.angle / 2.))
        cx = (width - 1.0) / 2. - cam.shift_x * max_resolution
        cy = (height - 1.0) / 2. + cam.shift_y * max_resolution

        xs, ys = np.meshgrid(np.arange(dist.shape[1]), np.arange(dist.shape[0]))
        
        # coordinate distances to principal point
        x_opt = np.abs(xs-cx)
        y_opt = np.abs(ys-cy)

        # Solve 3 equations in Wolfram Alpha: 
        # Solve[{X == (x-c0)/f0*Z, Y == (y-c1)/f0*Z, X*X + Y*Y + Z*Z = d*d}, {X,Y,Z}]
        depth = dist * f / np.sqrt(x_opt**2 + y_opt**2 + f**2)

        return depth
    
    @staticmethod
    def _get_pixel_neighbors(data, i, j):
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
    def _get_pixel_neighbors_stacked(img, filter_size=3, return_list=False):
        """
        Stacks the neighbors of each pixel according to a square filter around each given pixel in the depth dimensions.
        The neighbors are represented by shifting the input image in all directions required to simulate the filter.

        :param img: Input image. Type: blender object of type image.
        :param filter_size: Filter size. Type: int. Default: 5..
        :param return_list: Instead of stacking in the output array, just return a list of the "neighbor" images along with the input image.
        :return: Either a tensor with the "neighbor" images stacked in a separate additional dimension, or a list of images of the same shape as the input image, containing the shifted images (simulating the neighbors) and the input image.
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
                shifted[max(p, 0):min(rows, rows + p), max(q, 0):min(cols, cols + q)] = img[max(-p, 0):min(rows - p, rows),
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
    def _determine_noisy_pixels(image):
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
        noise_vals = [h[0] for h in hist if h[1] <= 100]  # Assuming the stray pixels wouldn't have a count of more than 100
        noise_indices = np.argwhere(PostProcessingUtility._isin(image, noise_vals))
        
        return noise_indices
    
    @staticmethod
    def remove_segmap_noise(image):
        """
        A function that takes an image and a few 2D indices, where these indices correspond to pixel values in
        segmentation maps, where these values are not real labels, but some deviations from the real labels, that were
        generated as a result of Blender doing some interpolation, smooting, or other numerical operations.
        
        Assumes that noise pixel values won't occur more than 100 times.

        :param image: ndarray of the .exr segmap
        :return: The denoised segmap image
        """
        
        noise_indices = PostProcessingUtility._determine_noisy_pixels(image)

        for index in noise_indices:
            neighbors = PostProcessingUtility._get_pixel_neighbors(image, index[0], index[1])  # Extracting the indices surrounding 3x3 neighbors
            curr_val = image[index[0]][index[1]][0]  # Current value of the noisy pixel

            neighbor_vals = [image[neighbor[0]][neighbor[1]] for neighbor in neighbors]  # Getting the values of the neighbors
            neighbor_vals = np.unique(np.array([np.array(index) for index in neighbor_vals]))  # Getting the unique values only

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
    
    @staticmethod
    def oil_paint_filter(image, filter_size=5, edges_only=True, rgb=False):
        """ Applies the oil paint filter on a single channel image (or more than one channel, where each channel is a replica
            of the other). This could be desired for corrupting rendered depth maps to appear more realistic. Also trims the
            redundant channels if they exist.
            
            :param image: Input image. Type: blender object of type image. 
            :param filter_size: Filter size, should be an odd number. Type: int. Default: 5
            :param edges_only: If true, applies the filter on the edges only. Default: True
            :param rgb: Apply the filter on an RGB image (if the image has 3 channels, they're assumed to not be replicated). Type: bool. Default: False
            :return: filtered image
        """
                
        import cv2
        from scipy import stats
        
        if rgb:
            intensity_img = (np.sum(image, axis=2) / 3.0)

            neighbors = np.array(PostProcessingUtility._get_pixel_neighbors_stacked(image, filter_size, return_list=True))
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
            if len(image.shape) == 3 and image.shape[2] > 1:
                image = image[:, :, 0]

            filtered_img = stats.mode(PostProcessingUtility._get_pixel_neighbors_stacked(image, filter_size), axis=2)[0] \
                .reshape(filtered_img.shape[0], filtered_img.shape[1])

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
    
    @staticmethod
    def trim_redundant_channels(image):
        """
        :param image: The image data.
        :return: The trimmed image data.
        """
        if len(image.shape) > 2:
            image = image[:, :, 0] # All channles have the same value, so just extract any single channel
        
        return image