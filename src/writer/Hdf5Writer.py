import csv
import json
import os

import bpy
import h5py
import numpy as np

from src.writer.Writer import Writer
from src.utility.BlenderUtility import load_image
from src.utility.Utility import Utility


class Hdf5Writer(Writer):
    """ For each key frame merges all registered output files into one hdf5 file

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "append_to_existing_output", "If true, the names of the output hdf5 files will be chosen in a way such that "
                                    "there are no collisions with already existing hdf5 files in the output directory. "
                                    "Type: bool. Default: False"
        "compression", "The compression technique that should be used when storing data in a hdf5 file. Type: string."
        "delete_temporary_files_afterwards", "True, if all temporary files should be deleted after merging. "
                                             "Type: bool. Default value: True."
       "stereo_separate_keys", "If true, stereo images are saved as two separate images *_0 and *_1. Type: bool. "
                                "Default: False (stereo images are combined into one np.array (2, ...))."
        "avoid_rendering", "If true, exit. Type: bool. Default: False."
    """

    def __init__(self, config):
        Writer.__init__(self, config)
        self._avoid_rendering = config.get_bool("avoid_rendering", False)

    def run(self):
        if self._avoid_rendering:
            print("Avoid rendering is on, no output produced!")
            return

        if self.config.get_bool("append_to_existing_output", False):
            frame_offset = 0
            # Look for hdf5 file with highest index
            for path in os.listdir(self._determine_output_dir(False)):
                if path.endswith(".hdf5"):
                    index = path[:-len(".hdf5")]
                    if index.isdigit():
                        frame_offset = max(frame_offset, int(index) + 1)
        else:
            frame_offset = 0

        # Go through all frames
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):

            # Create output hdf5 file
            hdf5_path = os.path.join(self._determine_output_dir(False), str(frame + frame_offset) + ".hdf5")
            with h5py.File(hdf5_path, "w") as f:

                if 'output' not in bpy.context.scene:
                    print("No output was designed in prior models!")
                    return
                # Go through all the output types
                print("Merging data for frame " + str(frame) + " into " + hdf5_path)

                for output_type in bpy.context.scene["output"]:
                    use_stereo = output_type["stereo"]
                    # Build path (path attribute is format string)
                    file_path = output_type["path"]
                    if '%' in file_path:
                        file_path = file_path % frame

                    if use_stereo:
                        path_l, path_r = self._get_stereo_path_pair(file_path)

                        img_l, new_key, new_version = self._load_and_postprocess(path_l, output_type["key"],
                                                                                   output_type["version"])
                        img_r, new_key, new_version = self._load_and_postprocess(path_r, output_type["key"],
                                                                                   output_type["version"])

                        if self.config.get_bool("stereo_separate_keys", False):
                            self._write_to_hdf_file(f, new_key + "_0", img_l)
                            self._write_to_hdf_file(f, new_key + "_1", img_r)
                        else:
                            data = np.array([img_l, img_r])
                            self._write_to_hdf_file(f, new_key, data)

                    else:
                        data, new_key, new_version = self._load_and_postprocess(file_path, output_type["key"],
                                                                                output_type["version"])

                        self._write_to_hdf_file(f, new_key, data)

                    self._write_to_hdf_file(f, new_key + "_version", np.string_([new_version]))

    def _write_to_hdf_file(self, file, key, data):
        """ Adds the given data as a new entry to the given hdf5 file.

        :param file: The hdf5 file handle.
        :param key: The key at which the data should be stored in the hdf5 file. Type: string.
        :param data: The data to store.
        """
        if data.dtype.char == 'S':
            file.create_dataset(key, data=data, dtype=data.dtype)
        else:
            file.create_dataset(key, data=data, compression=self.config.get_string("compression", 'gzip'))

    def _load_file(self, file_path):
        """ Tries to read in the file with the given path into a numpy array.

        :param file_path: The file path. Type: string.
        :return: A numpy array containing the data of the file.
        """
        if not os.path.exists(file_path):
            raise Exception("File not found: " + file_path)

        file_ending = file_path[file_path.rfind(".") + 1:].lower()

        if file_ending in ["exr", "png", "jpg"]:
            return load_image(file_path)
        elif file_ending in ["npy", "npz"]:
            return self._load_npy(file_path)
        elif file_ending in ["csv"]:
            return self._load_csv(file_path)
        else:
            raise NotImplementedError("File with ending " + file_ending + " cannot be loaded.")

    def _load_npy(self, file_path):
        """ Load the npy/npz file at the given path.

        :param file_path: The path. Type: string.
        :return: The content of the file
        """
        return np.load(file_path)

    def _load_csv(self, file_path):
        """ Load the csv file at the given path.

        :param file_path: The path. Type: string.
        :return: The content of the file
        """
        rows = []
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                rows.append(row)
        return np.string_(json.dumps(rows))  # make the list of dicts as a string

    def _get_stereo_path_pair(self, file_path):
        """
        Returns stereoscopic file path pair for a given "normal" image file path.
        :param file_path: The file path of a single image. Type: string.
        :return: The pair of file paths corresponding to the stereo images,
        """
        path_split = file_path.split(".")
        path_l = "{}_L.{}".format(path_split[0], path_split[1])
        path_r = "{}_R.{}".format(path_split[0], path_split[1])

        return path_l, path_r
