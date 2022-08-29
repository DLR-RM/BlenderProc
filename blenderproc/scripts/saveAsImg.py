""" Save a hdf5 container as image """

import argparse
import os
from typing import Optional

import h5py
import numpy as np

try:
    from visHdf5Files import vis_data
except ModuleNotFoundError:
    from blenderproc.scripts.visHdf5Files import vis_data


def save_array_as_image(array, key, file_path):
    """ Save array as an image, using the vis_data function"""
    vis_data(key, array, None, "", save_to_file=file_path)


def convert_hdf(base_file_path: str, output_folder: Optional[str] = None):
    """ Convert a hdf5 file to images """
    if os.path.exists(base_file_path):
        if os.path.isfile(base_file_path):
            base_name = str(os.path.basename(base_file_path)).split('.', maxsplit=1)[0]
            if output_folder is not None:
                base_name = os.path.join(output_folder, base_name)
            with h5py.File(base_file_path, 'r') as data:
                print(f"{base_file_path}:")
                for key, val in data.items():
                    val = np.array(val)
                    if np.issubdtype(val.dtype, np.string_) or len(val.shape) == 1:
                        pass  # metadata
                    else:
                        print(f"key: {key} {val.shape} {val.dtype.name}")

                        if val.shape[0] != 2:
                            # mono image
                            file_path = f'{base_name}_{key}.png'
                            save_array_as_image(val, key, file_path)
                        else:
                            # stereo image
                            for image_index, image_value in enumerate(val):
                                file_path = f'{base_name}_{key}_{image_index}.png'
                                save_array_as_image(image_value, key, file_path)
        else:
            print("The path is not a file")
    else:
        print(f"The file does not exist: {base_file_path}")


def cli():
    """
    Command line function
    """
    parser = argparse.ArgumentParser("Script to save images out of a hdf5 files.")
    parser.add_argument('hdf5', nargs='+', help='Path to hdf5 file/s')
    parser.add_argument('--output_dir', default=None,
                        help="Determines where the data is going to be saved. Default: Current directory")

    args = parser.parse_args()

    if isinstance(args.hdf5, str):
        convert_hdf(args.hdf5, args.output_dir)
    elif isinstance(args.hdf5, list):
        for file in args.hdf5:
            convert_hdf(file, args.output_dir)
    else:
        print("Input must be a path")


if __name__ == "__main__":
    cli()
