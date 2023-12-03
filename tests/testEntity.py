import blenderproc as bproc

import unittest

from blenderproc.python.tests.SilentMode import SilentMode
from blenderproc.python.types.EntityUtility import convert_to_entity_subclass, Entity
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.types.MeshObjectUtility import MeshObject


class UnitTestCheckUtility(unittest.TestCase):

    def test_convert_to_entity_subclass(self):
        """ Test if the blender_data objects are still valid after an undo execution is done.
        """
        bproc.clean_up(True)
        cube = convert_to_entity_subclass(bproc.object.create_primitive("CUBE").blender_obj)
        empty = convert_to_entity_subclass(bproc.object.create_empty("empty_test").blender_obj)
        light = convert_to_entity_subclass(bproc.types.Light().blender_obj)

        self.assertEqual(type(cube), MeshObject)
        self.assertEqual(type(empty), Entity)
        self.assertEqual(type(light), Light)

    def test_scene_graph_hierarchy_changes(self):
        bproc.clean_up(True)

        root = bproc.object.create_primitive("CUBE")
        root.set_location([1, 0, 0])

        # 1. Add child to root
        child = bproc.object.create_empty("empty")
        child.set_location([2, 0, 0])
        child.set_parent(root)
        print(child.get_location())

        self.assertEqual(child.get_parent(), root)
        self.assertEqual(type(child.get_parent()), MeshObject)
        self.assertTrue((child.get_local2world_mat()[:3, 3] == [2, 0, 0]).all())
        self.assertEqual(root.get_children(), [child])

        # 2. Move root
        root.set_location([2, 0, 0])
        self.assertTrue((child.get_local2world_mat()[:3, 3] == [3, 0, 0]).all())

        # 2. Add grandchild to child
        grandchild = bproc.types.Light()
        grandchild.set_location([4, 0, 0])
        grandchild.set_parent(child)

        self.assertEqual(grandchild.get_parent(), child)
        self.assertEqual(type(grandchild.get_parent()), Entity)
        self.assertTrue((grandchild.get_local2world_mat()[:3, 3] == [4, 0, 0]).all())
        self.assertEqual(child.get_children(), [grandchild])

        # 3. Clear parent of child
        child.clear_parent()

        # Check child
        self.assertEqual(child.get_parent(), None)
        self.assertTrue((child.get_local2world_mat()[:3, 3] == [3, 0, 0]).all())
        self.assertEqual(root.get_children(), [])
        # Check grandchild
        self.assertEqual(grandchild.get_parent(), child)
        self.assertEqual(type(grandchild.get_parent()), Entity)
        self.assertTrue((grandchild.get_local2world_mat()[:3, 3] == [4, 0, 0]).all())
        self.assertEqual(child.get_children(), [grandchild])

        # 4. Make grandchild a child of root
        grandchild.set_parent(root)

        self.assertEqual(grandchild.get_parent(), root)
        self.assertEqual(type(grandchild.get_parent()), MeshObject)
        self.assertTrue((grandchild.get_local2world_mat()[:3, 3] == [4, 0, 0]).all())
        self.assertEqual(root.get_children(), [grandchild])
        self.assertEqual(child.get_children(), [])

    def test_duplicate_linked(self):
        bproc.clean_up(True)

        cube = bproc.object.create_primitive("CUBE")
        duplicate_cube = cube.duplicate(linked=True)
        self.assertEqual(cube.blender_obj.data, duplicate_cube.blender_obj.data)

        empty = bproc.object.create_empty("empty")
        duplicate_empty = empty.duplicate(linked=True)
        self.assertEqual(duplicate_empty.blender_obj.data, None)

        light = Light()
        duplicate_light = light.duplicate(linked=True)
        self.assertEqual(light.blender_obj.data, duplicate_light.blender_obj.data)

    def test_duplicate_hierarchy(self):
        bproc.clean_up(True)

        root = bproc.object.create_primitive("CUBE")
        child = bproc.object.create_primitive("CUBE")
        grandchild = bproc.object.create_primitive("CUBE")

        grandchild.set_location([1, 1, 1])
        grandchild.set_parent(child)

        child.set_location([1, 1, 1])
        child.set_parent(root)

        duplicate_root = root.duplicate()
        duplicate_child = duplicate_root.get_children()[0]
        duplicate_grandchild = duplicate_child.get_children()[0]

        # world location
        self.assertTrue((duplicate_root.get_local2world_mat()[:3, 3] == [0, 0, 0]).all())
        self.assertTrue((duplicate_child.get_local2world_mat()[:3, 3] == [1, 1, 1]).all())
        self.assertTrue((duplicate_grandchild.get_local2world_mat()[:3, 3] == [2, 2, 2]).all())

        # relative location
        self.assertTrue((duplicate_root.get_location() == [0, 0, 0]).all())
        self.assertTrue((duplicate_child.get_location() == [1, 1, 1]).all())
        self.assertTrue((duplicate_grandchild.get_location() == [1, 1, 1]).all())
