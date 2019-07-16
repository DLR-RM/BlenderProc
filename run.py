# blender --background --python run.py  -- <config> [<args>]
import bpy
import sys

# Make sure the current script directory is in PATH, so we can load other python modules
dir = "."  # From CLI

if not dir in sys.path:
    sys.path.append(dir)

# Read args
argv = sys.argv
argv = argv[argv.index("--") + 1:]
working_dir = bpy.data.filepath

from src.main.Pipeline import Pipeline

config_path = argv[0]

pipeline = Pipeline(config_path, argv[1:], working_dir)
pipeline.run()