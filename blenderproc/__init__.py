import sys

# Only import if we are in the blender environment (TODO find a better solution)
if sys.executable.endswith("python3.9"):
    from .python.utility.SetupUtility import SetupUtility
    SetupUtility.setup([])
    from . import loader
    from . import utility
    from . import math
    from .python.utility.Initializer import init
    from . import postprocessing
    from . import writer
    from . import material
    from . import lighting
    from . import camera
    from . import renderer
