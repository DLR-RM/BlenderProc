from src.main.Module import Module
from scipy import stats

import numpy as np
import cv2


def get_neighbors_stacked(img, filter_size=3):
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

    return np.dstack(tuple(channels))


class OilPaintFilter(Module):
    """
    Applies the oil paint filter on a single channel image (or more than one channel, where each channel is a replica
    of the other). This could be desired for corrupting rendered depth maps to appear more realistic. Also trims the
    redundant channels if they exist.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       "filter_size", "Mode filter size."
       "edges_only", "If true, applies the filter on the edges only."
    """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image):
        if len(image.shape) == 3 and img.shape[2] > 1:
            image = image[:, :, 0]

        filtered_img = stats.mode(get_neighbors_stacked(image, self.config.get_int("filter_size"), 5), axis=2)[0]\
            .reshape(filtered_img.shape[0], filtered_img.shape[1])

        if self.config.get_bool("edges_only", True):
            __img = np.uint8(image)
            edges = cv2.Canny(__img, 0, np.max(__img))
            image[edges > 0] = filtered_img[edges > 0]
            filtered_img = image
        return filtered_img
