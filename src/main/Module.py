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
            bpy.context.scene["output"] += [output]
        else:
            bpy.context.scene["output"] = [output]

    def _register_output(self, default_prefix, default_key, suffix):
        """ Registers new output type using configured key and file prefix.

        :param default_prefix: The default prefix of the generated files.
        :param default_key: The default key which should be used for storing the output in merged file.
        :param suffix: The suffix of the generated files.
        """
        self._add_output_entry({
            "key": self.config.get_string("output_key", default_key),
            "path": os.path.join(self.output_dir, self.config.get_string("output_file_prefix", default_prefix)) + "%04d" + suffix
        })