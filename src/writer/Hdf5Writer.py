import csv
import json
import os
import shutil

import bpy
import h5py
import numpy as np

from src.main.Module import Module
from src.utility.Utility import Utility
from src.utility.BlenderUtility import load_image


class Hdf5Writer(Module):
    """ For each key frame merges all registered output files into one hdf5 file

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "compression", "The compression technique that should be used when storing data in a hdf5 file."
       "delete_temporary_files_afterwards", "True, if all temporary files should be deleted after merging."
       "postprocessing_modules", "A dict of list of postprocessing modules. The key in the dict specifies the output to which the postprocessing modules should be applied. Every postprocessing module has to have a run function which takes in the raw data and returns the processed data."
       "append_to_existing_output", "If true, the names of the output hdf5 files will be chosen in a way such that there are no collisions with already existing hdf5 files in the output directory."
       "stereo_separate_keys", "If true, stereo images are saved as two separate images *_0 and *_1. Default: false, stereo images are combined into one np.array (2, ...).
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self._avoid_rendering = config.get_bool("avoid_rendering", False)
        self.postprocessing_modules_per_output = {}
        module_configs = config.get_raw_dict("postprocessing_modules", {})
        for output_key in module_configs:
            self.postprocessing_modules_per_output[output_key] = Utility.initialize_modules(module_configs[output_key], {})

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

                        img_l = self._load_and_postprocess(path_l, output_type["key"])
                        img_r = self._load_and_postprocess(path_r, output_type["key"])

                        if self.config.get_bool("stereo_separate_keys", False):
                            self._write_to_hdf_file(f, output_type["key"] + "_0", img_l)
                            self._write_to_hdf_file(f, output_type["key"] + "_1", img_r)
                        else:
                            data = np.array([img_l, img_r])
                            self._write_to_hdf_file(f, output_type["key"], data)
                    else:
                        data = self._load_and_postprocess(file_path, output_type["key"])
                        self._write_to_hdf_file(f, output_type["key"], data)

                    # Write version number of current output at key_version
                    self._write_to_hdf_file(f, output_type["key"] + "_version", np.string_([output_type["version"]]))

    def _write_to_hdf_file(self, file, key, data):
        """ Adds the given data as a new entry to the given hdf5 file.

        :param file: The hdf5 file handle.
        :param key: The key at which the data should be stored in the hdf5 file.
        :param data: The data to store.
        """
        if data.dtype.char == 'S':
            file.create_dataset(key, data=data, dtype=data.dtype)
        else:
            file.create_dataset(key, data=data, compression=self.config.get_string("compression", 'gzip'))

    def _load_file(self, file_path):
        """ Tries to read in the file with the given path into a numpy array.

        :param file_path: The file path.
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

        :param file_path: The path.
        :return: The content of the file
        """
        return np.load(file_path)

    def _load_csv(self, file_path):
        """ Load the csv file at the given path.

        :param file_path: The path.
        :return: The content of the file
        """
        rows = []
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                rows.append(row)
        return np.string_(json.dumps(rows)) # make the list of dicts as a string

    def _apply_postprocessing(self, output_key, data):
        """ Applies all postprocessing modules registered for this output type.

        :param output_key: The key of the output type.
        :param data: The numpy data
        :return: The modified numpy data after doing the postprocessing
        """
        if output_key in self.postprocessing_modules_per_output:
            for module in self.postprocessing_modules_per_output[output_key]:
                data = module.run(data)

        return data

    def _load_and_postprocess(self, file_path, key):
        """
        Loads an image and post process it.
        :param file_path: Image path.
        :param key: The image's key with regards to the hdf5 file.
        :return: The post-processed image that was loaded using the file path.
        """
        data = self._load_file(Utility.resolve_path(file_path))

        data = self._apply_postprocessing(key, data)

        print("Key: " + key + " - shape: " + str(data.shape) + " - dtype: " + str(
            data.dtype) + " - path: " + file_path)

        return data

    def _get_stereo_path_pair(self, file_path):
        """
        Returns stereoscopic file path pair for a given "normal" image file path.
        :param file_path: The file path of a single image.
        :return: The pair of file paths corresponding to the stereo images,
        """
        path_split = file_path.split(".")
        path_l = "{}_L.{}".format(path_split[0], path_split[1])
        path_r = "{}_R.{}".format(path_split[0], path_split[1])

        return path_l, path_r
