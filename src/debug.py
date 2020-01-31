# This file can be used to execute the pipeline from the blender scripting UI
import os
import bpy
import sys

# Make sure the current script directory is in PATH, so we can load other python modules
working_dir = os.path.dirname(bpy.context.space_data.text.filepath) + "/../"

if not working_dir in sys.path:
    sys.path.append(working_dir)

# Add path to custom packages inside the blender main directory
if platform == "linux" or platform == "linux2":
    packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "custom-python-packages"))
elif platform == "darwin":
    packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "Resources", "custom-python-packages"))
else:
    raise Exception("This system is not supported yet: {}".format(platform))
sys.path.append(packages_path)

# Delete all loaded models inside src/, as they are cached inside blender
for module in list(sys.modules.keys()):
    if module.startswith("src"):
        del sys.modules[module]
        
from src.utility.ConfigParser import ConfigParser
from src.utility.Utility import Utility

from src.main.Pipeline import Pipeline

config_path = "examples/bop/config.yaml"

argv = ['/volume/pekdat/datasets/public/bop/original/tless', '/tmp/output_bop']
Utility.working_dir = working_dir

config_parser = ConfigParser()
config = config_parser.parse(Utility.resolve_path(config_path), argv) # Don't parse placeholder args in batch mode.
setup_config = config["setup"]

if "bop_toolkit_path" in setup_config:
    sys.path.append(setup_config["bop_toolkit_path"])
else:
    print('ERROR: Please download the bop_toolkit package and set bop_toolkit_path in config:')
    print('https://github.com/thodan/bop_toolkit')


# Focus the 3D View, this is necessary to make undo work (otherwise undo will focus on the scripting area)
for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

try:
    pipeline = Pipeline(config_path, [], working_dir)
    pipeline.run()
finally:
    # Revert back to previous view
    bpy.ops.screen.back_to_previous()
