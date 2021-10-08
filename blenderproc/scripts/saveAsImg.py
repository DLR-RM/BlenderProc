import argparse
import os
import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np




def process_img(img, key):
    if 'distance' in key or 'depth' in key or 'seg' in key:
        img = img.astype(np.float)
        if not "seg" in key:
            min_val = np.min(img)
            img -= min_val
        max_val = np.max(img)
        if "seg" in key:
            max_val = 36.0
            print("Assuming, there are 36 total classes (NYU), if there are more this will cause a bug!")
        if max_val != np.inf:
            img /= max_val
        else:
            img /= np.max(img)
        # clipping to avoid image errors
        img = np.clip(img, 0.0, 1.0)
        if len(img.shape) == 3:
            img = img[:, :, 0]
    elif 'flow' in key:
        try:
            # This import here is ugly, but else everytime someone uses this script it demands opencv and the progressbar
            sys.path.append(os.path.join(os.path.dirname(__file__)))
            from utils import flow_to_rgb
        except ImportError:
            raise ImportError("Using .hdf5 containers, which contain flow images needs opencv-python and progressbar "
                              "to be installed!")

        img = flow_to_rgb(img)
    elif "normals" in key:
        img = np.clip(img, 0.0, 1.0)
    return img


def save_array_as_image(array, key, file_path):
    if len(array.shape) == 2 or len(array.shape) == 3 and array.shape[2] == 3:
        val = process_img(array, key)
        if len(val.shape) == 2 or len(val.shape) == 3 and val.shape[2] == 1:
            plt.imsave(file_path, val, cmap='jet', vmin=0.0, vmax=1.0)
        else:
            plt.imsave(file_path, val)

    elif len(array.shape) == 3 and array.shape[2] == 4:
        val = process_img(array, key)
        plt.imsave(file_path, val)

    #error message if shape is incorrect
    else:
        print("Can't save numpy array with shape {} as an image".format(array.shape))



def convert_hdf(base_file_path, output_folder=None):
    if os.path.exists(base_file_path):
        if os.path.isfile(base_file_path):
            base_name = str(os.path.basename(base_file_path)).split('.')[0]
            if output_folder is not None:
                base_name = os.path.join(output_folder, base_name)
            with h5py.File(base_file_path, 'r') as data:
                print("{}:".format(base_file_path))
                keys = [key for key in data.keys()]
                for key in keys:
                    val = np.array(data[key])
                    if np.issubdtype(val.dtype, np.string_) or len(val.shape) == 1:
                        pass  # metadata
                    else:
                        print("key: {}  {} {}".format(key, val.shape, val.dtype.name))

                        if val.shape[0] != 2:
                            # mono image
                            file_path = '{}_{}.png'.format(base_name, key)
                            save_array_as_image(val, key, file_path)
                        else:
                            # stereo image
                            for image_index, image_value in enumerate(val):
                                file_path = '{}_{}_{}.png'.format(base_name, key, image_index)
                                save_array_as_image(image_value, key, file_path)
        else:
            print("The path is not a file")
    else:
        print("The file does not exist: {}".format(base_file_path))


def cli():
    parser = argparse.ArgumentParser("Script to save images out of a hdf5 files")
    parser.add_argument('hdf5', nargs='+', help='Path to hdf5 file/s')
    args = parser.parse_args()

    if isinstance(args.hdf5, str):
        convert_hdf(args.hdf5)
    elif isinstance(args.hdf5, list):
        for file in args.hdf5:
            convert_hdf(file)
    else:
        print("Input must be a path")

if __name__ == "__main__":
    cli()