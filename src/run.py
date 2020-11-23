# blender --background --python run.py  -- <config> [<args>]
import sys
import os
from sys import platform


# Make sure the current script directory is in PATH, so we can load other python modules
dir = "."  # From CLI
if not dir in sys.path:
    sys.path.append(dir)

# Add path to custom packages inside the blender main directory
if platform == "linux" or platform == "linux2":
    packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "custom-python-packages"))
elif platform == "darwin":
    packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "Resources", "custom-python-packages"))
elif platform == "win32":
    packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "custom-python-packages"))
else:
    raise Exception("This system is not supported yet: {}".format(platform))
sys.path.append(packages_path)

# Read args
argv = sys.argv
batch_index_file = None

if "--batch-process" in argv:
    batch_index_file = argv[argv.index("--batch-process") + 1]

argv = argv[argv.index("--") + 1:]
working_dir = os.path.dirname(os.path.abspath(__file__))

from src.main.Pipeline import Pipeline
from src.utility.Utility import Utility

config_path = argv[0]
temp_dir = argv[1]
if batch_index_file == None:
    pipeline = Pipeline(config_path, argv[2:], working_dir, temp_dir)
    pipeline.run()
else:
    with open(Utility.resolve_path(batch_index_file), "r") as f:
        lines = f.readlines()

        for line in lines:
            args = line.split(" ")
            pipeline = Pipeline(config_path, args, working_dir, temp_dir)
            pipeline.run()
