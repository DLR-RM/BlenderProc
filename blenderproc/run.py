""" The main run script, has to be parsed to the blender python environment """

# blender --background --python cli.py  -- <config> [<args>]
import sys

# Make sure the current script directory is in PATH, so we can load other python modules
directory = "."  # From CLI
if directory not in sys.path:
    sys.path.append(directory)

# Read args
argv = sys.argv
argv = argv[argv.index("--") + 1:]

# pylint: disable=wrong-import-position
from blenderproc.python.utility.SetupUtility import SetupUtility
# pylint: enable=wrong-import-position

# Setup general required pip packages e.q. pyyaml
packages_path = SetupUtility.setup_pip([])
sys.path.append(packages_path)

# pylint: disable=wrong-import-position
from blenderproc.python.modules.main.Pipeline import Pipeline
# pylint: enable=wrong-import-position

config_path = argv[0]
temp_dir = argv[1]

pipeline = Pipeline(config_path, argv[2:], temp_dir)
pipeline.run()
