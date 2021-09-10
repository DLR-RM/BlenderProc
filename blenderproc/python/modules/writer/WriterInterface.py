import os
import numpy as np

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.utility.Utility import Utility, resolve_path
from blenderproc.python.writer.WriterUtility import WriterUtility

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
        self.write_alpha_channel = self.config.get_bool("write_alpha_channel", False)

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
        if self._avoid_output:
            print("Avoid output is on, no output produced!")
            return

        file_prefix = self.config.get_string("output_file_prefix", default_file_prefix)
        path_prefix = os.path.join(self._determine_output_dir(), file_prefix)
        item_writer.write_items_to_file(path_prefix, items, self.config.get_list("attributes_to_write", default_attributes), world_frame_change=self.destination_frame)
        Utility.register_output(self._determine_output_dir(), file_prefix, self.config.get_string("output_key", default_output_key), ".npy", version)
            
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
        data = WriterUtility.load_output_file(resolve_path(file_path), self.write_alpha_channel, remove=False)
        data, new_key, new_version = self._apply_postprocessing(key, data, version)
        if isinstance(data, np.ndarray):
            print("Key: " + key + " - shape: " + str(data.shape) + " - dtype: " + str(data.dtype) + " - path: " + file_path)
        else:
            print("Key: " + key + " - path: " + file_path)
        return data, new_key, new_version

