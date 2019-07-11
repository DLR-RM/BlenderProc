# blender --background --python run.py  -- <config> [<args>]
import os
import bpy
import sys
import importlib

# Make sure the current script directory is in PATH, so we can load other python modules
if bpy.context.space_data is None:
    dir = "."  # From CLI
else:
    dir = os.path.dirname(bpy.context.space_data.text.filepath)  # From inside blender

if not dir in sys.path:
    sys.path.append(dir)

# Read args
started_from_commandline = '--' in sys.argv
if started_from_commandline:
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
else:
    # Reload all models inside src/, as they are cached inside blender
    for module in sys.modules.keys():
        if module.startswith("src"):
            print(module)
            importlib.reload(sys.modules[module])
    argv = ["config/debug.json"]


from src.main.Pipeline import Pipeline

config_path = argv[0]

pipeline = Pipeline(config_path, argv[1:])
pipeline.run()
