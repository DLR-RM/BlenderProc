import os
import bpy
os.environ["INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT"] = "1"
import blenderproc as bproc

# This file attempts to load all downloaded Haven textures.
# Not a real test yet, just what I'm using for now.

home = os.path.expanduser("~")
haven_folder = os.path.join(home, "assets", "haven")
haven_textures_folder = os.path.join(haven_folder, "textures")
texture_names = os.listdir(haven_textures_folder)
texture_names.sort()

failures = 0
for texture_name in texture_names:
    bproc.api.loader.load_haven_mat(haven_textures_folder, [texture_name])

    if texture_name not in bpy.data.materials:
        print(f"{texture_name} failed to load.")
        failures += 1

total = len(texture_names)
successes = total - failures
print(f"Succesfully loaded {successes}/{total} Haven textures.")
