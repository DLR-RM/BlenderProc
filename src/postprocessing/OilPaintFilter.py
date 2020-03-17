from src.main.Module import Module
from scipy import stats

import numpy as np
import cv2


def get_neighbors_stacked(img, filter_size=3, return_list=False):
    """
    Stacks the neighbors of each pixel according to a square filter around each given pixel in the depth dimensions.
    The neighbors are represented by shifting the input image in all directions required to simulate the filter.
    :param img: Input image.
    :param filter_size: Filter size.
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


class OilPaintFilter(Module):
    """
    Applies the oil paint filter on a single channel image (or more than one channel, where each channel is a replica
    of the other). This could be desired for corrupting rendered depth maps to appear more realistic. Also trims the
    redundant channels if they exist.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       "filter_size", "Mode filter size, should be an odd number. Type: int. Optional. Default value: 5"
       "edges_only", "If true, applies the filter on the edges only. For RGB images, they should be represented in uint8 arrays. Type: bool. Optional. Default value: True"
       "rgb", "Apply the filter on an RGB image (if the image has 3 channels, they're assumed to not be replicated). Type: bool. Default value: False" 
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image):
        filter_size = self.config.get_int("filter_size", 5)
        edges_only = self.config.get_bool("edges_only", True)

        if self.config.get_bool("rgb", False):
            intensity_img = (np.sum(image, axis=2) / 3.0)

            neighbors = np.array(get_neighbors_stacked(image, filter_size, return_list=True))
            neighbors_intensity = get_neighbors_stacked(intensity_img, filter_size)

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
            if len(image.shape) == 3 and img.shape[2] > 1:
                image = image[:, :, 0]

            filtered_img = stats.mode(get_neighbors_stacked(image, filter_size), axis=2)[0] \
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
