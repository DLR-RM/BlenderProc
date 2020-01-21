# This file can be used to execute the pipeline from the blender scripting UI
import os
import bpy
import sys

# Make sure the current script directory is in PATH, so we can load other python modules
working_dir = os.path.dirname(bpy.context.space_data.text.filepath) + "/../"

if not working_dir in sys.path:
    sys.path.append(working_dir)

# Add path to custom packages inside the blender main directory
sys.path.append(os.path.join(os.path.dirname(sys.executable), "custom-python-packages"))

# Delete all loaded models inside src/, as they are cached inside blender
for module in list(sys.modules.keys()):
    if module.startswith("src"):
        del sys.modules[module]

from src.utility.BlenderUtility import check_bb_intersection

cube = bpy.context.scene.objects['Cube']
sphere = bpy.context.scene.objects['Sphere']


print(check_bb_intersection(cube, sphere))
print(check_bb_intersection(sphere, cube))