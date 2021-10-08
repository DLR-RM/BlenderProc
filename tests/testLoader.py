import blenderproc as bproc
import unittest
import os.path

resource_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources")

class UnitTestCheckLoader(unittest.TestCase):

    def test_object_loader(self):
        """ Tests if the object loader is loading all objects from a given .obj file.
        """
        bproc.init()
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
        bproc.init()
        materials = bproc.loader.load_ccmaterials(used_assets=["metal", "wood", "fabric"])

        list_of_some_textures = ["Metal001", "Fabric006", "Wood050"]

        for material in materials:
            if material.get_name() in list_of_some_textures:
                list_of_some_textures.remove(material.get_name())

        # If the list is not empty, not all object have been loaded
        self.assertEqual(list_of_some_textures, [])
