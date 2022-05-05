# blender --background --python cli.py  -- <config> [<args>]
import sys
import os
from sys import platform


# Make sure the current script directory is in PATH, so we can load other python modules
dir = "."  # From CLI
if not dir in sys.path:
    sys.path.append(dir)

# Read args
argv = sys.argv
argv = argv[argv.index("--") + 1:]

from blenderproc.python.utility.SetupUtility import SetupUtility
# Setup general required pip packages e.q. pyyaml
packages_path = SetupUtility.setup_pip([])
sys.path.append(packages_path)

from blenderproc.python.modules.main.Pipeline import Pipeline

config_path = argv[0]
temp_dir = argv[1]

pipeline = Pipeline(config_path, argv[2:], temp_dir)
pipeline.run()
