import os
import sys
from .version import __version__

# check the python version, only python 3.X is allowed:
if sys.version_info.major < 3:
    raise Exception("BlenderProc requires at least python 3.X to run.")

# Only import if we are in the blender environment, this environment variable is set by the cli.py script
if "INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT" in os.environ:
    # Remove the parent of the blender proc folder, as it might contain other packages
    # that we do not want to import inside the blenderproc env
    sys.path.remove(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from .python.utility.SetupUtility import SetupUtility
    SetupUtility.setup([])
    from .api import loader
    from .api import utility
    from .api import sampler
    from .api import math
    from .python.utility.Initializer import init
    from .api import postprocessing
    from .api import writer
    from .api import material
    from .api import lighting
    from .api import camera
    from .api import renderer
    from .api import world
    from .api import constructor
    from .api import object
    from .api import types
    from .api import filter
else:
    # this checks if blenderproc the command line tool or the cli.py script are used. If not an exception is thrown
    import traceback
    # extract the basename of the file, which is the first in the traceback
    file_names_of_stack = [os.path.basename(file_summary.filename) for file_summary in traceback.extract_stack()]
    first_file_name = file_names_of_stack[0]
    # check if the name of this file is either blenderproc or if the "OUTSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT_BUT_IN_RUN_SCRIPT" is set, which is set in the cli.py
    is_correct_startup_script = first_file_name != "blenderproc" and first_file_name != "command_line.py"
    if "OUTSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT_BUT_IN_RUN_SCRIPT" not in os.environ and is_correct_startup_script:
        raise Exception(f"\n###############\nThis script can only be run by \"blenderproc run\", instead of calling:\n\tpython {sys.argv[0]}\ncall:\n\tblenderproc run {sys.argv[0]}\n###############")
