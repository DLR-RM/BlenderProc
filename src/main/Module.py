import bpy
import os

from src.utility.Utility import Utility

class Module:

    def __init__(self, config):
        self.config = config
        self.output_dir = Utility.resolve_path(self.config.get_string("output_dir", ""))
        os.makedirs(self.output_dir, exist_ok=True)

    def _add_output_entry(self, output):
        """ Registers the given output in the scene's custom properties

        :param output: A dict containing key and path of the new output type.
        """
        if "output" in bpy.context.scene:
            if not self._output_already_registered(output, bpy.context.scene["output"]): # E.g. multiple camera samplers
                bpy.context.scene["output"] += [output]
        else:
            bpy.context.scene["output"] = [output]

    def _register_output(self, default_prefix, default_key, suffix, version):
        """ Registers new output type using configured key and file prefix.

        :param default_prefix: The default prefix of the generated files.
        :param default_key: The default key which should be used for storing the output in merged file.
        :param suffix: The suffix of the generated files.
        :param version: The version number which will be stored at key_version in the final merged file.
        """
        self._add_output_entry({
            "key": self.config.get_string("output_key", default_key),
            "path": os.path.join(self.output_dir, self.config.get_string("output_file_prefix", default_prefix)) + "%04d" + suffix,
            "version": version
        })

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
                return  True
            if output["key"] == _output["key"] or output["path"] == _output["path"]:
                raise Exception("Can not have two output entries with the same key/path but not same path/key." +
                                "Original entry's data: key:{} path:{}, Entry to be registered: key:{} path:{}"
                                .format(_output["key"], _output["path"], output["key"], output["path"]))

        return False
