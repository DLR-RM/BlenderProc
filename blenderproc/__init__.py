import sys

# Only import if we are in the blender environment (TODO find a better solution)
if sys.executable.endswith("python3.9"):
    from . import loader
    from . import camera
