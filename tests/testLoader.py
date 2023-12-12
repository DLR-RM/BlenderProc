import blenderproc as bproc

import unittest
import os.path
from pathlib import Path

import bpy

from blenderproc.python.tests.TestsPathManager import test_path_manager


class UnitTestCheckLoader(unittest.TestCase):

    def test_object_loader(self):
        """ Tests if the object loader is loading all objects from a given .obj file.
        """
        bproc.clean_up(True)
        resource_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources")
        objs = bproc.loader.load_obj(os.path.join(resource_folder, "scene.obj"))

        # List of objects in the loaded "../examples/resources.obj"
        list_of_objects = ["Cube", "Cube.001", "Icosphere", "Icosphere.001", "Icosphere.002", "Suzanne", "Cylinder",
                           "Cylinder.001", "Cylinder.002"]

        for obj in objs:
            list_of_objects.remove(obj.get_name())

        # If the list is not empty, not all object have been loaded
        self.assertEqual(list_of_objects, [])

    def test_cc_material_loader(self):
        """ Tests if the default cc materials are loaded.
        """
        bproc.clean_up(True)
        cc_texture_folder = test_path_manager.cc_materials
        materials = bproc.loader.load_ccmaterials(folder_path=cc_texture_folder,
                                                  used_assets=["metal", "wood", "fabric"])

        list_of_some_textures = ["Metal001", "Fabric004", "Wood039"]

        for material in materials:
            if material.get_name() in list_of_some_textures:
                list_of_some_textures.remove(material.get_name())

        # If the list is not empty, not all object have been loaded
        self.assertEqual(list_of_some_textures, [])

    def test_create_material_from_texture(self):
        """
        Tests if the material creation from texture function works
        """

        def perform_material_checks(used_material: bproc.types.Material, used_path: Path):
            # check if the material has a texture loaded
            found_nodes = used_material.get_nodes_with_type("ShaderNodeTexImage")
            self.assertEqual(len(found_nodes), 1)
            texture_node = found_nodes[0]

            # check if this loaded node uses the specified texture
            loaded_filepath = Path(texture_node.image.filepath).absolute()
            self.assertEqual(str(loaded_filepath), str(used_path.absolute()))

        # test with a path to a file:
        texture_path = Path(__file__).parent.parent / "images" / "material_manipulation_sample_texture.jpg"
        material = bproc.material.create_material_from_texture(texture_path, material_name="new_mat")
        perform_material_checks(material, texture_path)

        # load a texture beforehand and construct a material from that
        texture = bpy.data.images.load(str(texture_path), check_existing=True)
        material = bproc.material.create_material_from_texture(texture, material_name="new_mat")
        perform_material_checks(material, texture_path)
