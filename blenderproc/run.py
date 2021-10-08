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
    packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", "..", "custom-python-packages"))
elif platform == "darwin":
    packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", "..", "..", "Resources", "custom-python-packages"))
elif platform == "win32":
    packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", "..", "custom-python-packages"))
else:
    raise Exception("This system is not supported yet: {}".format(platform))
sys.path.append(packages_path)

# Read args
argv = sys.argv
argv = argv[argv.index("--") + 1:]

from blenderproc.python.utility.SetupUtility import SetupUtility
# Setup general required pip packages e.q. pyyaml
SetupUtility.setup_pip([])

from blenderproc.python.modules.main.Pipeline import Pipeline

config_path = argv[0]
temp_dir = argv[1]

pipeline = Pipeline(config_path, argv[2:], temp_dir)
pipeline.run()
