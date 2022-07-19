import blenderproc as bproc
from blenderproc.python.tests.TestsPathManager import test_path_manager
import os
import unittest
import bpy

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
        """Loads all downloaded Haven textures and check whether a corresponding Blender material was created. This 
        test does not yet check whether all texture maps were loaded and does not ensure the matieral looks correct.
        """
        haven_textures_folder = os.path.join(test_path_manager.haven, "textures")
        texture_names = os.listdir(haven_textures_folder)
        texture_names.sort()

        successes = 0
        for texture_name in texture_names:
            if texture_name in textures_to_ignore:
                continue
            bproc.api.loader.load_haven_mat(haven_textures_folder, [texture_name])
            if texture_name in bpy.data.materials:
                successes += 1

        total = len(texture_names) - len(textures_to_ignore)

        assert_message = f"Loaded {successes}/{total} Haven textures succesfully."
        self.assertEqual(successes, total, assert_message)

    def test_new_random_haven_material(self):
        """
        Test if one can load a random texture from the haven dataset
        """

        cube = bproc.object.create_primitive("CUBE")
        for used_asset in [None, ["terrain_red_01"]]:
            # set a completely random haven material
            mat = bproc.loader.load_haven_mat(test_path_manager.haven, return_random_element=True,
                                              used_assets=used_asset)
            cube.replace_materials(mat)

            # check if after loading exactly one material is there
            materials = cube.get_materials()
            self.assertEqual(len(materials), 1)

            # check if images where loaded
            material = materials[0]
            texture_nodes = material.get_nodes_with_type("ShaderNodeTexImage")
            self.assertGreater(len(texture_nodes), 3)



if __name__ == '__main__':
    unittest.main()
