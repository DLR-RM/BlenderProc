
from src.utility.Config import Config
from src.utility.Utility import Utility
import bpy

class Pipeline:

    def __init__(self, config_path, args, working_dir):
        Utility.working_dir = working_dir

        # Remove all objects from the default scene
        for obj in bpy.context.scene.objects:
            obj.select_set(True)
        bpy.ops.object.delete()

        config = Config.read_config_dict(Utility.resolve_path(config_path), args)

        self.modules = Utility.initialize_modules(config["modules"], config["global"])

    def run(self):
        """ Runs each module and measuring their execution time. """
        with Utility.BlockStopWatch("Running blender pipeline"):
            for module in self.modules:
                with Utility.BlockStopWatch("Running module " + module.__class__.__name__):
                    module.run()

