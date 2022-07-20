# This file can be used to execute the pipeline from the blender scripting UI
import os
import bpy
import sys

# Add path to custom packages inside the blender main directory
from blenderproc.python.utility.SetupUtility import SetupUtility
python_bin, packages_path, packages_import_path, pre_python_package_path = SetupUtility.determine_python_paths(None, None)
sys.path.append(packages_import_path)

from blenderproc.python.modules.main.Pipeline import Pipeline

# Replace placeholders manually or use --debug command line argument
config_path = "###CONFIG_PATH###"
args = ["###CONFIG_ARGS###"]  # Put in here arguments to use for filling the placeholders in the config file.

# Focus the 3D View, this is necessary to make undo work (otherwise undo will focus on the scripting area)
for window in bpy.context.window_manager.windows:
    screen = window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            override = {'window': window, 'screen': screen, 'area': area}
            bpy.ops.screen.screen_full_area(override)
            break

# Store temp files in the same directory for debugging
temp_dir = "examples/debugging/temp"

try:
    # In this debug case the rendering is avoided, everything is executed except the final render step
    # For the RgbRenderer the undo is avoided to have a direct way of rendering in debug
    pipeline = Pipeline(config_path, args, temp_dir, avoid_output=True)
    pipeline.run()
finally:
    # Revert back to previous view
    bpy.ops.screen.back_to_previous()
