import json

from src.utility.Utility import Utility
import re
import bpy

class Pipeline:

    def __init__(self, config_path, args, working_dir):
        Utility.working_dir = working_dir

        config = self._read_config_dict(config_path, args)

        self.modules = Utility.initialize_modules(config["modules"], config["global"])

    def _read_config_dict(self, config_path, args):
        with open(Utility.resolve_path(config_path), "r") as f:
            json_text = f.read()

            # Remove comments
            json_text = re.sub(r'^//.*\n?', '', json_text, flags=re.MULTILINE)
            # Replace arguments
            for i, arg in enumerate(args):
                json_text = json_text.replace("<args:" + str(i) + ">", arg)

            if "<args:" in json_text:
                raise Exception("Too less arguments given")

            config = json.loads(json_text)
        return config

    def run(self):
        for module in self.modules:
            with Utility.BlockStopWatch("Running module " + module.__class__.__name__):
                module.run()

