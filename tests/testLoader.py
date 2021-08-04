import unittest
import os.path

from src.utility.loader.ObjectLoader import ObjectLoader
from src.utility.Initializer import Initializer

resource_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources")

class UnitTestCheckLoader(unittest.TestCase):

    def test_object_loader(self):
        """ Tests if the object loader is loading all objects from a given .obj file.
        """
        Initializer.init()
        objs = ObjectLoader.load(os.path.join(resource_folder, "scene.obj"))

        # List of objects in the loaded "../examples/resources.obj"
        list_of_objects = ["Cube", "Cube.001", "Icosphere", "Icosphere.001", "Icosphere.002", "Suzanne", "Cylinder",
                           "Cylinder.001", "Cylinder.002"]

        for obj in objs:
            list_of_objects.remove(obj.get_name())

        # If the list is not empty, not all object have been loaded
        self.assertEqual(list_of_objects, [])
