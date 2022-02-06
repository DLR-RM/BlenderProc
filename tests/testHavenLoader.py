import os
import unittest
import bpy
os.environ["INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT"] = "1"
import blenderproc as bproc

default_haven_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources", "haven")

# Currently ignoring these textures because they are not downloaded correctly.
# After issue #456 is fixed, these should be included again.
textures_to_ignore = [
    "book_pattern",
    "church_bricks_02",
    "fabric_pattern_05",
    "fabric_pattern_07",
    "leather_red_02",
    "leather_red_03"
]

class UnitTestCheckHavenLoader(unittest.TestCase):
    def test_load_all_downloaded_haven_textures(self):
        haven_folder = os.getenv("HAVEN_PATH", default=default_haven_folder)
        haven_textures_folder = os.path.join(haven_folder, "textures")
        texture_names = os.listdir(haven_textures_folder)
        texture_names.sort()

        failures = 0
        for texture_name in texture_names:
            if texture_name in textures_to_ignore:
                continue
            bproc.api.loader.load_haven_mat(haven_textures_folder, [texture_name])
            if texture_name not in bpy.data.materials:
                failures += 1

        total = len(texture_names)
        successes = total - failures

        print(f"Succesfully loaded {successes}/{total} Haven textures.")
        assert total == successes


if __name__ == '__main__':
    testRunner = unittest.runner.TextTestRunner()
    testRunner.run(UnitTestCheckHavenLoader.test_load_all_downloaded_haven_textures)
