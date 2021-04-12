
import os

from src.utility.ConfigParser import ConfigParser
from src.utility.SetupUtility import SetupUtility
from src.utility.Utility import Utility, Config
from src.main.GlobalStorage import GlobalStorage

class Pipeline:

    def __init__(self, config_path, args, working_dir, temp_dir, avoid_rendering=False):
        """
        Inits the pipeline, by calling the constructors of all modules mentioned in the config.

        :param config_path: path to the config
        :param args: arguments which were provided to the run.py and are specified in the config file
        :param working_dir: the current working dir usually the place where the run.py sits
        :param working_dir: the directory where to put temporary files during the execution
        :param avoid_rendering: if this is true all renderes are not executed (except the RgbRenderer, \
                               where only the rendering call to blender is avoided) with this it is possible to debug \
                               properly
        """
        Utility.working_dir = working_dir

        config_parser = ConfigParser(silent=True)
        config = config_parser.parse(Utility.resolve_path(config_path), args)

        # Setup pip packages specified in config
        SetupUtility.setup_pip(config["pip"] if "pip" in config else [])

        if avoid_rendering:
            GlobalStorage.add_to_config_before_init("avoid_rendering", True)

        Utility.temp_dir = Utility.resolve_path(temp_dir)
        os.makedirs(Utility.temp_dir, exist_ok=True)

        self.modules = Utility.initialize_modules(config["modules"])

    def run(self):
        """ Runs each module and measuring their execution time. """
        with Utility.BlockStopWatch("Running blender pipeline"):
            for module in self.modules:
                with Utility.BlockStopWatch("Running module " + module.__class__.__name__):
                    module.run()
