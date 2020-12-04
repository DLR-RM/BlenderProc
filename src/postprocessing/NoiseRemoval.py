import numpy as np

from src.main.Module import Module


class NoiseRemoval(Module):
    """Removes noise pixels.

    Assumes that noise pixel values won't occur more than 100 times.
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def _get_neighbors(self, data, i, j):
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

    def _remove_noise(self, image, noise_indices):
        """
        A function that takes an image and a few 2D indices, where these indices correspond to pixel values in
        segmentation maps, where these values are not real labels, but some deviations from the real labels, that were
        generated as a result of Blender doing some interpolation, smooting, or other numerical operations.

        :param image: ndarray of the .exr segmap
        :param noise_indices: a list of 2D indices that correspond to the noisy pixels. One criteria of finding \
                              these pixels is to use a histogram and find the pixels with frequencies lower than \
                              a threshold, e.g. 100.
        """

        for index in noise_indices:
            neighbors = self._get_neighbors(image, index[0], index[1])  # Extracting the indices surrounding 3x3 neighbors
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

    def _isin(self, element, test_elements, assume_unique=False, invert=False):
        """ As np.isin is only available after v1.13 and blender is using 1.10.1 we have to implement it manually. """
        element = np.asarray(element)
        return np.in1d(element, test_elements, assume_unique=assume_unique, invert=invert).reshape(element.shape)

    def run(self, image, key, version):
        """
        :param image: The image data.
        :param key: The key to use when writing to the .hdf5.
        :param version: Version of the original data.
        :return: The cleaned image data, key to use when writing and version numer.
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
        noise_indices = np.argwhere(self._isin(image, noise_vals))

        return self._remove_noise(image, noise_indices), key, version
