
import unittest
import os.path

from src.utility.loader.ObjectLoader import ObjectLoader
from src.utility.Utility import Utility
from src.utility.Initializer import Initializer

resource_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources")

class UnitTestCheckUtility(unittest.TestCase):

    def test_blender_reference_after_undo(self):
        """ Test if the blender_data objects are still valid after an undo execution is done. 
        """
        Initializer.init()
        objs = ObjectLoader.load(os.path.join(resource_folder, "scene.obj"))

        for obj in objs:
            obj.set_cp("test", 0)

        with Utility.UndoAfterExecution():
            for obj in objs:
                obj.set_cp("test", 1)

        for obj in objs:
            self.assertEqual(obj.get_cp("test"), 0)
