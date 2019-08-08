import bpy
import os

from src.utility.Utility import Utility

class Module:

    def __init__(self, config):
        self.config = config
        self.output_dir = Utility.resolve_path(self.config.get_string("output_dir"))
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

    def _add_output_entry(self, output):
        if "output" in bpy.context.scene:
            bpy.context.scene["output"] += [output]
        else:
            bpy.context.scene["output"] = [output]

    def _register_output(self, default_prefix, default_key, suffix):
        # Store output path and configured key into the scene's custom properties
        self._add_output_entry({
            "key": self.config.get_string("output_key", default_key),
            "path": os.path.join(self.output_dir, self.config.get_string("output_file_prefix", default_prefix)) + "%04d" + suffix
        })