"""A procedural Blender pipeline for photorealistic rendering."""

import os
import sys
from .version import __version__
from .python.utility.SetupUtility import SetupUtility, is_using_external_bpy_module

# If "USE_EXTERNAL_BPY_MODULE" is set, we expect the bpy module is provided from the outside
if is_using_external_bpy_module():
    try:
        import bpy
        if bpy.app.version[0] != 4 and bpy.app.version[1] != 2:
            raise RuntimeError("\n###############\nUSE_EXTERNAL_BPY_MODULE is set, but bpy module is not from Blender 4.2.\n\tpip install bpy==4.2.0\n###############\n")

        print(f"BlenderProc is using external 'bpy' ({bpy.app.version_string}) module found in the environment.")
        # If we successfully imported bpy of correct version, we can signal that we are in the internal blender python environment
        os.environ.setdefault("INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT", "1")
    except ImportError:
        raise RuntimeError("\n###############\nUSE_EXTERNAL_BPY_MODULE is set, but bpy module could not be imported. Make sure bpy module is present in your python environment.\n\tpip install bpy==4.2.0\n###############\n")


# check the python version, only python 3.X is allowed:
if sys.version_info.major < 3:
    raise Exception("BlenderProc requires at least python 3.X to run.")

# exr is now disabled by default (see https://github.com/opencv/opencv/issues/21326)
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1" 

# Only import if we are in the blender environment, this environment variable is set by the cli.py script
if "INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT" in os.environ:
    # Remove the parent of the blender proc folder, as it might contain other packages
    # that we do not want to import inside the blenderproc env
    sys.path.remove(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    # Also clean the python path as this might disturb the pip installs
    if "PYTHONPATH" in os.environ:
        del os.environ["PYTHONPATH"]
    
    if not is_using_external_bpy_module():
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
    is_module_call = file_names_of_stack[0] == "runpy.py" or file_names_of_stack[0] == "blenderproc-script.py"
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
            and not is_correct_startup_command and not is_using_external_bpy_module():
        # pylint: disable=consider-using-f-string
        raise RuntimeError("\n###############\nThis script can only be run by \"blenderproc run\", instead of calling:"
                           "\n\tpython {}\ncall:\n\tblenderproc run {}\n\nor consider using 'USE_EXTERNAL_BPY_MODULE=1'"
                           "\n###############".format(sys.argv[0], sys.argv[0]))
        # pylint: enable=consider-using-f-string
