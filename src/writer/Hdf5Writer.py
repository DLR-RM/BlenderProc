from src.main.Module import Module
import bpy
import h5py
import os
from src.utility.Utility import Utility
import imageio
import numpy as np
import csv
import json

class Hdf5Writer(Module):

    def __init__(self, config):
        Module.__init__(self, config)

        self.postprocessing_modules_per_output = {}
        module_configs = config.get_raw_dict("postprocessing_modules", {})
        for output_key in module_configs:
            self.postprocessing_modules_per_output[output_key] = Utility.initialize_modules(module_configs[output_key], {})

    def run(self):
        """ For each key frame merges all registered output files into one hdf5 file"""
        output_dir = Utility.resolve_path(self.config.get_string("output_dir"))

        # Go through all frames
        for frame in range(1, bpy.context.scene.frame_end + 1):

            # Create output hdf5 file
            hdf5_path = os.path.join(output_dir, str(frame) + ".hdf5")
            with h5py.File(hdf5_path, "w") as f:

                # Go through all the output types
                print("Merging data for frame " + str(frame) + " into " + hdf5_path)
                for output_type in bpy.context.scene["output"]:

                    # Build path (path attribute is format string)
                    file_path = output_type["path"] 
                    if '%' in file_path:
                        file_path = file_path % frame

                    data = self._load_file(Utility.resolve_path(file_path))

                    # in case the data is string, just store it
                    if type(data) == str:
                        f.create_dataset(output_type["key"], data=np.string_(data), dtype="S10")
                        print("Key: " + output_type["key"] + "str - path: " + file_path)
                    # otherwise its numbers, so apply postprocessing if applicable
                    else:
                        data = self._apply_postprocessing(output_type["key"], data)
                        print("Key: " + output_type["key"] + " - shape: " + str(data.shape) + " - dtype: " + str(data.dtype) + " - path: " + file_path)
                        f.create_dataset(output_type["key"], data=data, compression=self.config.get_string("compression", 'gzip'))

                    # Write version number of current output at key_version
                    f.create_dataset(output_type["key"] + "_version", data=np.string_([output_type["version"]]), dtype="S10")

                    if self.config.get_bool("delete_original_files_afterwards", True):
                        os.remove(file_path)

    def _load_file(self, file_path):
        """ Tries to read in the file with the given path into a numpy array.

        :param file_path: The file path.
        :return: A numpy array containing the data of the file.
        """
        if not os.path.exists(file_path):
            raise Exception("File not found: " + file_path)

        file_ending = file_path[file_path.rfind(".") + 1:].lower()

        if file_ending in ["exr", "png", "jpg"]:
            return self._load_image(file_path)
        elif file_ending in ["npy", "npz"]:
            return self._load_npy(file_path)
        elif file_ending in ["csv"]:
            return self._load_csv(file_path)
        else:
            raise NotImplementedError("File with ending " + file_ending + " cannot be loaded.")

    def _load_image(self, file_path):
        """ Load the image at the given path returns its pixels as a numpy array.

        The alpha channel is neglected.

        :param file_path: The path to the image.
        :return: The numpy array
        """
        return imageio.imread(file_path)[:, :, :3]

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
        l = []
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                l.append(row)
        l = json.dumps(l) # make the list of dicts as a string
        return l

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

