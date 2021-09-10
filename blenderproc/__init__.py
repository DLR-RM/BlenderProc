import sys

# Only import if we are in the blender environment (TODO find a better solution)
if sys.executable.endswith("python3.9"):
    from .python.utility.SetupUtility import SetupUtility
    SetupUtility.setup([])
    from . import loader
    from . import material
    from .python.types.MaterialUtility import Material
    from . import camera
    from . import renderer
