
import shutil
import os
import bpy

from src.utility.ConfigParser import ConfigParser
from src.utility.Utility import Utility, Config
from src.main.GlobalStorage import GlobalStorage

class Pipeline:

    def __init__(self, config_path, args, working_dir, temp_dir, should_perform_clean_up=True, avoid_rendering=False):
        """
        Inits the pipeline, by calling the constructors of all modules mentioned in the config.

        :param config_path: path to the config
        :param args: arguments which were provided to the run.py and are specified in the config file
        :param working_dir: the current working dir usually the place where the run.py sits
        :param working_dir: the directory where to put temporary files during the execution
        :param should_perform_clean_up: if the generated temp file should be deleted at the end
        :param avoid_rendering: if this is true all renderes are not executed (except the RgbRenderer, \
                               where only the rendering call to blender is avoided) with this it is possible to debug \
                               properly
        """
        Utility.working_dir = working_dir

        # Clean up example scene or scene created by last run when debugging pipeline inside blender
        if should_perform_clean_up:
            self._cleanup() 

        config_parser = ConfigParser(silent=True)
        config = config_parser.parse(Utility.resolve_path(config_path), args)

        if avoid_rendering:
            GlobalStorage.add_to_config_before_init("avoid_rendering", True)

        Utility.temp_dir = Utility.resolve_path(temp_dir)
        os.makedirs(Utility.temp_dir, exist_ok=True)

        self.modules = Utility.initialize_modules(config["modules"])


    def _cleanup(self):
        """ Resets the scene to its clean state, but keeping the UI as it is """
        # Switch to right context
        if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode='OBJECT')

        # Clean up
        self._remove_all_data()
        self._remove_custom_properties()

        # Create new world
        new_world = bpy.data.worlds.new("World")
        bpy.context.scene.world = new_world

    def _remove_all_data(self):
        """ Remove all data blocks except opened scripts and the default scene. """
        # Go through all attributes of bpy.data
        for collection in dir(bpy.data):
            data_structure = getattr(bpy.data, collection)
            # Check that it is a data collection
            if isinstance(data_structure, bpy.types.bpy_prop_collection) and hasattr(data_structure, "remove") and collection not in ["texts"]:
                # Go over all entities in that collection
                for block in data_structure:
                    # Remove everything besides the default scene
                    if not isinstance(block, bpy.types.Scene) or block.name != "Scene":
                        data_structure.remove(block)

    def _remove_custom_properties(self):
        """ Remove all custom properties registered at global entities like the scene. """
        for key in bpy.context.scene.keys():
            del bpy.context.scene[key]

    def run(self):
        """ Runs each module and measuring their execution time. """
        with Utility.BlockStopWatch("Running blender pipeline"):
            for module in self.modules:
                with Utility.BlockStopWatch("Running module " + module.__class__.__name__):
                    module.run()
