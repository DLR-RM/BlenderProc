import os
import csv
import json
import bpy
import h5py
import numpy as np

import mathutils

from src.main.Module import Module
from src.utility.BlenderUtility import load_image
from src.utility.MathUtility import MathUtility
from src.utility.Utility import Utility

class WriterInterface(Module):
    """
    Parent class for all other writers classes, it had the functionality to return objects attributes and write \
    them to file and to load and process post processing modules

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - postprocessing_modules
          - A dict of list of postprocessing modules. The key in the dict specifies the output to which the
            postprocessing modules should be applied. Every postprocessing module has to have a run function which
            takes in the raw data and returns the processed data. 
          - dict
        * - destination_frame
          - Used to transform point to blender coordinate frame. Default: ["X", "Y", "Z"]
          - list
        * - attributes_to_write
          - A list of attribute names that should written to file. The next table lists all attributes that can be
            used here. 
          - list
        * - output_file_prefix
          - The prefix of the file that should be created.
          - string
        * - output_key
          - The key which should be used for storing the output in a merged file.
          - string
        * - write_alpha_channel
          - If true, the alpha channel will be written to file. Default: False.
          - bool
    """
    def __init__(self, config):
        Module.__init__(self, config)
        self.postprocessing_modules_per_output = {}
        module_configs = config.get_raw_dict("postprocessing_modules", {})
        for output_key in module_configs:
            self.postprocessing_modules_per_output[output_key] = Utility.initialize_modules(module_configs[output_key])
        self.name_to_id = {}
        self.destination_frame = self.config.get_list("destination_frame", ["X", "Y", "Z"])


    def write_attributes_to_file(self, item_writer, items, default_file_prefix, default_output_key, default_attributes, version="1.0.0"):
        """ Writes the state of the given items to a file with the configured prefix.

        This method also registers the corresponding output.

        :param item_writer: The item writer object to use. Type: object.
        :param items: The list of items. Type: list.
        :param default_file_prefix: The default file name prefix to use. Type: string.
        :param default_output_key: The default output key to use. Type: string.
        :param default_attributes: The default attributes to write, if no attributes are specified in the config. Type: list.
        :param version: The version to use when registering the output. Type: string.
        """
        file_prefix = self.config.get_string("output_file_prefix", default_file_prefix)
        path_prefix = os.path.join(self._determine_output_dir(), file_prefix)
        item_writer.write_items_to_file(path_prefix, items, self.config.get_list("attributes_to_write", default_attributes))
        Utility.register_output(self._determine_output_dir(), file_prefix, self.config.get_string("output_key", default_output_key), ".npy", version)

    def _get_attribute(self, item, attribute_name):
        """ Returns the value of the requested attribute for the given item.

        This method covers all general attributes that blender objects have.

        :param item: The item. Type: blender object.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """
        if attribute_name == "id":
            if item.name not in self.name_to_id:
                self.name_to_id[item.name] = len(self.name_to_id.values())
            return self.name_to_id[item.name]
        elif attribute_name == "name":
            return item.name
        elif attribute_name == "location":
            return MathUtility.transform_point_to_blender_coord_frame(item.location, self.destination_frame)
        elif attribute_name == "rotation_euler":
            return MathUtility.transform_point_to_blender_coord_frame(item.rotation_euler, self.destination_frame)
        elif attribute_name == "rotation_forward_vec":
            # Calc forward vector from rotation matrix
            rot_mat = item.rotation_euler.to_matrix()
            forward = rot_mat @ mathutils.Vector([0, 0, -1])
            return MathUtility.transform_point_to_blender_coord_frame(forward, self.destination_frame)
        elif attribute_name == "rotation_up_vec":
            # Calc up vector from rotation matrix
            rot_mat = item.rotation_euler.to_matrix()
            up = rot_mat @ mathutils.Vector([0, 1, 0])
            return MathUtility.transform_point_to_blender_coord_frame(up, self.destination_frame)
        elif attribute_name == "matrix_world":
            # Transform matrix_world to given destination frame
            matrix_world = Utility.transform_matrix_to_blender_coord_frame(item.matrix_world, self.destination_frame)
            return [[x for x in c] for c in matrix_world]
        elif attribute_name.startswith("customprop_"):
            custom_property_name = attribute_name[len("customprop_"):]
            # Make sure the requested custom property exist
            if custom_property_name in item:
                return item[custom_property_name]
            else:
                raise Exception("No such custom property: " + custom_property_name)
        else:
            raise Exception("No such attribute: " + attribute_name)

    def _apply_postprocessing(self, output_key, data, version):
        """
        Applies all postprocessing modules registered for this output type.

        :param output_key: The key of the output type. Type: string
        :param data: The numpy data.
        :param version: The version number original data.
        :return: The modified numpy data after doing the postprocessing
        """
        if output_key in self.postprocessing_modules_per_output:
            for module in self.postprocessing_modules_per_output[output_key]:
                data, new_key, new_version = module.run(data, output_key, version)
        else:
            new_key = output_key
            new_version = version

        return data, new_key, new_version

    def _load_and_postprocess(self, file_path, key, version = "1.0.0"):
        """
        Loads an image and post process it.

        :param file_path: Image path. Type: string.
        :param key: The image's key with regards to the hdf5 file. Type: string.
        :param version: The version number original data. Type: String. Default: 1.0.0.
        :return: The post-processed image that was loaded using the file path.
        """
        data = self._load_file(Utility.resolve_path(file_path))
        data, new_key, new_version = self._apply_postprocessing(key, data, version)
        print("Key: " + key + " - shape: " + str(data.shape) + " - dtype: " + str(data.dtype) + " - path: " + file_path)
        return data, new_key, new_version

    def _load_file(self, file_path):
        """ Tries to read in the file with the given path into a numpy array.

        :param file_path: The file path. Type: string.
        :return: A numpy array containing the data of the file.
        """
        if not os.path.exists(file_path):
            raise Exception("File not found: " + file_path)

        file_ending = file_path[file_path.rfind(".") + 1:].lower()

        if file_ending in ["exr", "png", "jpg"]:
            #num_channels is 4 if transparent_background is true in config
            return load_image(file_path, num_channels = 3 + self.config.get_bool("write_alpha_channel", False))
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
