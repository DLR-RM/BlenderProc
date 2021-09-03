
import cv2
import numpy as np
from PIL import Image


def resize(img, new_size, method="nearest"):
    method = method.lower()
    if "lanczos" in method:
        return np.asarray(Image.fromarray(img).resize(new_size, Image.LANCZOS))
    elif "nearest" in method:
        return np.asarray(Image.fromarray(img).resize(new_size, Image.NEAREST))
    else:
        raise Exception("Unknown resizing method")


# https://github.com/kujason/ip_basic/blob/master/ip_basic/depth_map_utils.py
def fill_in_fast(depth_map, max_depth=100.0, custom_kernel=None,
                 extrapolate=False, blur_type='bilateral'):
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
    valid_pixels = (depth_map > 0.1)
    depth_map[valid_pixels] = max_depth - depth_map[valid_pixels]

    # Dilate
    depth_map = cv2.dilate(depth_map, custom_kernel)

    # Hole closing
    depth_map = cv2.morphologyEx(depth_map, cv2.MORPH_CLOSE, FULL_KERNEL_5)

    # Fill empty spaces with dilated values
    empty_pixels = (depth_map < 0.1)
    dilated = cv2.dilate(depth_map, FULL_KERNEL_7)
    depth_map[empty_pixels] = dilated[empty_pixels]

    # Extend highest pixel to top of image
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
        valid_pixels = (depth_map > 0.1)
        blurred = cv2.GaussianBlur(depth_map, (5, 5), 0)
        depth_map[valid_pixels] = blurred[valid_pixels]

    # Invert
    valid_pixels = (depth_map > 0.1)
    depth_map[valid_pixels] = max_depth - depth_map[valid_pixels]

    return depth_map
