import blenderproc as bproc

import unittest

from blenderproc.python.tests.SilentMode import SilentMode
from blenderproc.python.types.MeshObjectUtility import create_primitive
from blenderproc.python.material import MaterialLoaderUtility


class UnitTestCheckUtility(unittest.TestCase):
    def test_materials(self):
        bproc.clean_up(True)

        mat1 = MaterialLoaderUtility.create("mat1")
        mat2 = MaterialLoaderUtility.create("mat2")

        obj = create_primitive("CUBE")
        self.assertTrue(obj.has_materials() == False)

        obj.add_material(mat1)
        self.assertTrue(obj.materials() == 1)
        self.assertTrue(obj.get_material_slot_link(0) == "DATA")
        self.assertTrue(obj.get_material(0, "DATA").get_name() == "mat1")
        self.assertTrue(obj.get_material(0, "OBJECT") is None)
        self.assertTrue(obj.get_material(0, "VISIBLE").get_name() == "mat1")

        obj.set_material(0, mat2, "OBJECT")
        self.assertTrue(obj.get_material(0, "DATA").get_name() == "mat1")
        self.assertTrue(obj.get_material(0, "OBJECT").get_name() == "mat2")
        self.assertTrue(obj.get_material(0, "VISIBLE").get_name() == "mat1")

        obj.set_material_slot_link(0, "OBJECT")
        self.assertTrue(obj.get_material(0, "DATA").get_name() == "mat1")
        self.assertTrue(obj.get_material(0, "OBJECT").get_name() == "mat2")
        self.assertTrue(obj.get_material(0, "VISIBLE").get_name() == "mat2")

        obj.set_material(0, None, "OBJECT")
        self.assertTrue(obj.get_material(0, "DATA").get_name() == "mat1")
        self.assertTrue(obj.get_material(0, "OBJECT") is None)
        self.assertTrue(obj.get_material(0, "VISIBLE").get_name() == "mat1")
