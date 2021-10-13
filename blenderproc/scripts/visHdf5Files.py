import os
import h5py
import argparse
import numpy as np
from matplotlib import pyplot as plt
import sys
import json
import re

def cli():
    parser = argparse.ArgumentParser("Script to visualize hdf5 files")

    parser.add_argument('hdf5_paths', nargs='+', help='Path to hdf5 file/s')
    parser.add_argument('--keys', nargs='+', help='Keys that should be visualized. If none is given, all keys are visualized.', default=None)
    parser.add_argument('--rgb_keys', nargs='+', help='Keys that should be interpreted as rgb data.', default=["colors", "normals", "diffuse"])
    parser.add_argument('--flow_keys', nargs='+', help='Keys that should be interpreted as optical flow data.', default=["forward_flow", "backward_flow"])
    parser.add_argument('--segmap_keys', nargs='+', help='Keys that should be interpreted as segmentation data.', default=["segmap", ".*_segmaps"])
    parser.add_argument('--segcolormap_keys', nargs='+', help='Keys that point to the segmentation color maps corresponding to the configured segmap_keys.', default=["segcolormap"])
    parser.add_argument('--other_non_rgb_keys', nargs='+', help='Keys that contain additional non-RGB data which should be visualized using a jet color map.', default=["distance", "depth"])

    args = parser.parse_args()

    def key_matches(key, patterns, return_index=False):
        for p, pattern in enumerate(patterns):
            if re.fullmatch(pattern, key):
                return (True, p) if return_index else True

        return (False, None) if return_index else False

    def vis_data(key, data, full_hdf5_data, file_label):
        # If key is valid and does not contain segmentation data, create figure and add title
        if key_matches(key, args.flow_keys + args.rgb_keys + args.other_non_rgb_keys):
            plt.figure()
            plt.title("{} in {}".format(key, file_label))

        if key_matches(key, args.flow_keys):
            try:
                # This import here is ugly, but else everytime someone uses this script it demands opencv and the progressbar
                sys.path.append(os.path.join(os.path.dirname(__file__)))
                from utils import flow_to_rgb
            except ImportError:
                raise ImportError("Using .hdf5 containers, which contain flow images needs opencv-python and progressbar "
                                  "to be installed!")

            # Visualize optical flow
            plt.imshow(flow_to_rgb(data), cmap='jet')
        elif key_matches(key, args.segmap_keys):
            # Try to find labels for each channel in the segcolormap
            channel_labels = {}
            _, key_index = key_matches(key, args.segmap_keys, return_index=True)
            if key_index < len(args.segcolormap_keys):
                # Check if segcolormap_key for the current segmap key is configured and exists
                segcolormap_key = args.segcolormap_keys[key_index]
                if segcolormap_key in full_hdf5_data:
                    # Extract segcolormap data
                    segcolormap = json.loads(np.array(full_hdf5_data[segcolormap_key]).tostring())
                    if len(segcolormap) > 0:
                        # Go though all columns, we are looking for channel_* ones
                        for colormap_key, colormap_value in segcolormap[0].items():
                            if colormap_key.startswith("channel_") and colormap_value.isdigit():
                                channel_labels[int(colormap_value)] = colormap_key[len("channel_"):]

            # Make sure we have three dimensions
            if len(data.shape) == 2:
                data = data[:, :, None]
            # Go through all channels
            for i in range(data.shape[2]):
                # Try to determine label
                if i in channel_labels:
                    channel_label = channel_labels[i]
                else:
                    channel_label = i

                # Visualize channel
                plt.figure()
                plt.title("{} / {} in {}".format(key, channel_label, file_label))
                plt.imshow(data[:, :, i], cmap='jet')

        elif key_matches(key, args.other_non_rgb_keys):
            # Make sure the data has only one channel, otherwise matplotlib will treat it as an rgb image
            if len(data.shape) == 3:
                if data.shape[2] != 1:
                    print("Warning: The data with key '" + key + "' has more than one channel which would not allow using a jet color map. Therefore only the first channel is visualized.")
                data = data[:, :, 0]

            plt.imshow(data, cmap='summer')
        elif key_matches(key, args.rgb_keys):
            plt.imshow(data)


    def vis_file(path):
        # Check if file exists
        if os.path.exists(path):
            if os.path.isfile(path):
                with h5py.File(path, 'r') as data:
                    print(path + " contains the following keys: " + str(data.keys()))

                    # Select only a subset of keys if args.keys is given
                    if args.keys is not None:
                        keys = [key for key in data.keys() if key in args.keys]
                    else:
                        keys = [key for key in data.keys()]

                    # Visualize every key
                    for key in keys:
                        value = np.array(data[key])
                        # Check if it is a stereo image
                        if len(value.shape) >= 3 and value.shape[0] == 2:
                            # Visualize both eyes separately
                            for i, img in enumerate(value):
                                vis_data(key, img, data, os.path.basename(path) + (" (left)" if i == 0 else " (right)"))
                        else:
                            vis_data(key, value, data, os.path.basename(path))

            else:
                print("The path is not a file")
        else:
            print("The file does not exist: {}".format(args.hdf5))

    # Visualize all given files
    for path in args.hdf5_paths:
        vis_file(path)
    plt.show()

if __name__ == "__main__":
    cli()
