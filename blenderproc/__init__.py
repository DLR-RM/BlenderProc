import os
import sys

# Only import if we are in the blender environment, this environment variable is set by the run.py script
if "INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT" in os.environ:
    # Remove the parent of the blender proc folder, as it might contain other packages
    # that we do not want to import inside the blenderproc env
    sys.path.remove(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from .python.utility.SetupUtility import SetupUtility
    SetupUtility.setup([])
    from . import loader
    from . import utility
    from . import sampler
    from . import math
    from .python.utility.Initializer import init
    from . import postprocessing
    from . import writer
    from . import material
    from . import lighting
    from . import camera
    from . import renderer
    from . import world
    from . import constructor
    from . import object
    from . import types
    from . import filter
