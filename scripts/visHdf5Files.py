import os
import h5py
import argparse
import numpy as np
from matplotlib import pyplot as plt
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__)))
from utils import flow_to_rgb

parser = argparse.ArgumentParser("Script to visualize hdf5 files")

parser.add_argument('hdf5_paths', nargs='+', help='Path to hdf5 file/s')
parser.add_argument('--keys', nargs='+', help='Keys that should be visualized. If none is given, all keys are visualized.', default=None)
parser.add_argument('--rgb_keys', nargs='+', help='Keys that should be interpreted as rgb data.', default=["colors"])
parser.add_argument('--flow_keys', nargs='+', help='Keys that should be interpreted as optical flow data.', default=["forward_flow", "backward_flow"])
parser.add_argument('--segmap_keys', nargs='+', help='Keys that should be interpreted as segmentation data.', default=["segmap"])
parser.add_argument('--segcolormap_keys', nargs='+', help='Keys that point to the segmentation color maps corresponding to the configured segmap_keys.', default=["segcolormap"])
parser.add_argument('--other_non_rgb_keys', nargs='+', help='Keys that contain additional non-RGB data which should be visualized using a jet color map.', default=["normals", "distance", "depth"])

args = parser.parse_args()


def vis_data(key, data, full_hdf5_data, file_label):
    # If key is valid and does not contain segmentation data, create figure and add title
    if key in args.flow_keys + args.rgb_keys + args.other_non_rgb_keys:
        plt.figure()
        plt.title("{} in {}".format(key, file_label))

    if key in args.flow_keys:
        # Visualize optical flow
        plt.imshow(flow_to_rgb(data), cmap='jet')
    elif key in args.segmap_keys:
        # Try to find labels for each channel in the segcolormap
        channel_labels = {}
        if args.segmap_keys.index(key) < len(args.segcolormap_keys):
            # Check if segcolormap_key for the current segmap key is configured and exists
            segcolormap_key = args.segcolormap_keys[args.segmap_keys.index(key)]
            if segcolormap_key in full_hdf5_data:
                # Extract segcolormap data
                segcolormap = json.loads(np.array(full_hdf5_data[segcolormap_key]).tostring())
                if len(segcolormap) > 0:
                    # Go though all columns, we are looking for channel_* ones
                    for colormap_key, colormap_value in segcolormap[0].items():
                        if colormap_key.startswith("channel_") and colormap_value.isdigit():
                            channel_labels[int(colormap_value)] = colormap_key[len("channel_"):]

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

    elif key in args.other_non_rgb_keys:
        plt.imshow(data, cmap='jet')
    elif key in args.rgb_keys:
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
                    vis_data(key, data[key], data, os.path.basename(path))

        else:
            print("The path is not a file")
    else:
        print("The file does not exist: {}".format(args.hdf5))

# Visualize all given files
for path in args.hdf5_paths:
    vis_file(path)
plt.show()
