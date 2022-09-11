"""A procedural Blender pipeline for photorealistic rendering."""

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
    # Also clean the python path as this might disturb the pip installs
    if "PYTHONPATH" in os.environ:
        del os.environ["PYTHONPATH"]
    from .python.utility.SetupUtility import SetupUtility
    SetupUtility.setup([])
    from .api import loader
    from .api import utility
    from .api import sampler
    from .api import math
    from .python.utility.Initializer import init, clean_up
    from .api import postprocessing
    from .api import writer
    from .api import material
    from .api import lighting
    from .api import camera
    from .api import renderer
    from .api import world
    from .api import constructor
    from .api import types
    # pylint: disable=redefined-builtin
    from .api import object
    from .api import filter
    # pylint: enable=redefined-builtin
else:
    # this checks if blenderproc the command line tool or the cli.py script are used. If not an exception is thrown
    import traceback
    # extract the basename of the file, which is the first in the traceback
    stack_summary = traceback.extract_stack()
    file_names_of_stack = [os.path.basename(file_summary.filename) for file_summary in stack_summary]
    # check if blenderproc is called via python3 -m blenderproc ...
    is_module_call = file_names_of_stack[0] == "runpy.py"
    if sys.platform == "win32":
        is_bproc_shell_called = file_names_of_stack[2] in ["metadata.py", "__main__.py"]
        is_command_line_script_called = file_names_of_stack[0] == "command_line.py"

        is_correct_startup_command = is_bproc_shell_called or is_command_line_script_called or is_module_call
    else:
        is_bproc_shell_called = file_names_of_stack[0] in ["blenderproc", "command_line.py"]
        # check if the name of this file is either blenderproc or if the
        # "OUTSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT_BUT_IN_RUN_SCRIPT" is set, which is set in the cli.py
        is_correct_startup_command = is_bproc_shell_called or is_module_call
    if "OUTSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT_BUT_IN_RUN_SCRIPT" not in os.environ \
            and not is_correct_startup_command:
        # pylint: disable=consider-using-f-string
        raise RuntimeError("\n###############\nThis script can only be run by \"blenderproc run\", instead of calling:"
                           "\n\tpython {}\ncall:\n\tblenderproc run {}\n###############".format(sys.argv[0],
                                                                                                sys.argv[0]))
        # pylint: enable=consider-using-f-string
