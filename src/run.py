# blender --background --python run.py  -- <config> [<args>]
import bpy
import sys
import os

# Make sure the current script directory is in PATH, so we can load other python modules
dir = "."  # From CLI
if not dir in sys.path:
    sys.path.append(dir)

# Add path to custom packages inside the blender main directory
sys.path.append(os.path.join(os.path.dirname(sys.executable), "custom-python-packages"))

# Read args
argv = sys.argv
argv = argv[argv.index("--") + 1:]
working_dir = os.path.dirname(os.path.abspath(__file__))

from src.main.Pipeline import Pipeline

config_path = argv[0]

pipeline = Pipeline(config_path, argv[1:], working_dir)
pipeline.run()
