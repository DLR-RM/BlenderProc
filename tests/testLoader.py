import unittest
import os.path

from src.utility.loader.ObjectLoader import ObjectLoader
from src.utility.loader.CCMaterialLoader import CCMaterialLoader
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

    def test_cc_material_loader(self):
        """ Tests if the default cc materials are loaded.
        """
        Initializer.init()
        objs = CCMaterialLoader.load()

        #By default, does textures are loaded by the upper function call
        probably_useful_texture = ["paving stones", "tiles", "wood", "fabric", "bricks", "metal", "wood floor",
                                   "ground", "rock", "concrete", "leather", "planks", "rocks", "gravel",
                                   "asphalt", "painted metal", "painted plaster", "marble", "carpet",
                                   "plastic", "roofing tiles", "bark", "metal plates", "wood siding",
                                   "terrazzo", "plaster", "paint", "corrugated steel", "painted wood", "lava"
                                   "cardboard", "clay", "diamond plate", "ice", "moss", "pipe", "candy",
                                   "chipboard", "rope", "sponge", "tactile paving", "paper", "cork",
                                   "wood chips"]

        for obj in objs:
            probably_useful_texture.remove(obj.get_name())

        # If the list is not empty, not all object have been loaded
        self.assertEqual(probably_useful_texture, [])
