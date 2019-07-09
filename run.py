# blender --background --python run.py  -- <config> [<args>]
import os
import bpy
import sys
import importlib

# Make sure the current script directory is in PATH, so we can load other python modules
if bpy.context.space_data is None:
    dir = "."
else:
    dir = os.path.dirname(bpy.context.space_data.text.filepath)

if not dir in sys.path:
    sys.path.append(dir)

started_from_commandline = '--' in sys.argv
if started_from_commandline:
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
else:
    for module in sys.modules.keys():
        if module.startswith("src"):
            print(module)
            importlib.reload(sys.modules[module])
    argv = ["config/debug.json"]


from src.main.Pipeline import Pipeline

config_path = argv[0]

pipeline = Pipeline(config_path, argv[1:])
pipeline.run()
