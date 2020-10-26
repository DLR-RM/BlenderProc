import os

import bpy

from src.utility.Utility import Utility


class Module:
    """
    **Configuration**:

    All of these values can be set per Module or of the global config defined in the main.Initializer:

      "module": "main.Initializer",
      "config":{
        "global": {
          "output_dir": "<args:X>"
        }
      }

    If they are set globally all modules will inherit them, if there is no module defined key available.

    .. csv-table::
       :header: "Parameter", "Description"

       "output_is_temp", "If True, all files created in this module will be written into the temp_dir. If False,"
                         "the output_dir is used. Type: bool."
       "output_dir", "The path to a directory where all persistent output files should be stored. If it doesn't exist,"
                     "it is created automatically. Type: string. Default: ""."
    """

    def __init__(self, config):
        self.config = config
        self._default_init()

    def _default_init(self):
        """
        These operations are called during all modules inits
        """
        self._output_dir = Utility.resolve_path(self.config.get_string("output_dir", ""))
        # os.makedirs(self._output_dir, exist_ok=True)

        self._temp_dir = Utility.get_temporary_directory()

    def _determine_output_dir(self, output_is_temp_default=True):
        """ Returns the directory where to store output file created by this module.

        :param output_is_temp_default: True, if the files created by this module should be temporary by default.
        :return: The output directory to use
        """
        if self.config.get_bool("output_is_temp", output_is_temp_default):
            return self._temp_dir
        else:
            return self._output_dir

    def _add_output_entry(self, output):
        """ Registers the given output in the scene's custom properties

        :param output: A dict containing key and path of the new output type.
        """
        if "output" in bpy.context.scene:
            if not self._output_already_registered(output, bpy.context.scene["output"]): # E.g. multiple camera samplers
                bpy.context.scene["output"] += [output]
        else:
            bpy.context.scene["output"] = [output]

    def _register_output(self, default_prefix, default_key, suffix, version, stereo=False, unique_for_camposes=True, output_key_parameter_name="output_key", output_file_prefix_parameter_name="output_file_prefix"):
        """ Registers new output type using configured key and file prefix.

        :param default_prefix: The default prefix of the generated files.
        :param default_key: The default key which should be used for storing the output in merged file.
        :param suffix: The suffix of the generated files.
        :param version: The version number which will be stored at key_version in the final merged file.
        :param stereo: Boolean indicating whether the output of this rendering result will be stereo.
        :param unique_for_camposes: True if the output to be registered is unique for all the camera poses
        :param output_key_parameter_name: The parameter name to use for retrieving the output key from the config.
        :param output_file_prefix_parameter_name: The parameter name to use for retrieving the output file prefix from the config.
        """

        self._add_output_entry({
            "key": self.config.get_string(output_key_parameter_name, default_key),
            "path": os.path.join(self._determine_output_dir(), self.config.get_string(output_file_prefix_parameter_name, default_prefix)) + ("%04d" if unique_for_camposes else "") + suffix,
            "version": version,
            "stereo": stereo
        })

    def _find_registered_output_by_key(self, key):
        """ Returns the output which was registered with the given key.

        :param key: The output key to look for.
        :return: The dict containing all information registered for that output. If no output with the given key exists, None is returned.
        """
        if "output" in bpy.context.scene:
            for output in bpy.context.scene["output"]:
                if output["key"] == key:
                    return output.to_dict()

        return None

    def _output_already_registered(self, output, output_list):
        """ Checks if the given output entry already exists in the list of outputs, by checking on the key and path.
        Also throws an error if it detects an entry having the same key but not the same path and vice versa since this
        is ambiguous.

        :param output: The output dict entry.
        :param output_list: The list of output entries.
        :return: bool indicating whether it already exists.
        """
        for _output in output_list:
            if output["key"] == _output["key"] and output["path"] == _output["path"]:
                print("Warning! Detected output entries with duplicate keys and paths")
                return True
            if output["key"] == _output["key"] or output["path"] == _output["path"]:
                raise Exception("Can not have two output entries with the same key/path but not same path/key." +
                                "Original entry's data: key:{} path:{}, Entry to be registered: key:{} path:{}"
                                .format(_output["key"], _output["path"], output["key"], output["path"]))

        return False
