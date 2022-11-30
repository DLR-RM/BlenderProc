import blenderproc as bproc

import unittest
import os.path
import numpy as np

from blenderproc.python.tests.SilentMode import SilentMode
from blenderproc.python.tests.TestsPathManager import test_path_manager
from blenderproc.python.utility.Utility import UndoAfterExecution


class UnitTestCheckUtility(unittest.TestCase):

    def test_blender_reference_after_undo(self):
        """ Test if the blender_data objects are still valid after an undo execution is done. 
        """
        with SilentMode():
            bproc.clean_up(True)
            objs = bproc.loader.load_obj(os.path.join(test_path_manager.example_resources, "scene.obj"))

            for obj in objs:
                obj.set_cp("test", 0)

            with UndoAfterExecution():
                for obj in objs:
                    obj.set_cp("test", 1)

        for obj in objs:
            self.assertEqual(obj.get_cp("test"), 0)

    def test_math_util_transformation_mat(self):
        """ Tests if the transformation matrix is calculated correctly
        """

        # poi = np.array([0, 0, 0])
        location = np.array([1, 2, 3])
        # rotation = 0.0
        rotation_matrix = np.array([[-8.94427180e-01, -3.58568549e-01, 2.67261177e-01],
                                        [ 4.47213531e-01, -7.17137218e-01, 5.34522414e-01],
                                        [ 2.34371083e-08,  5.97614229e-01, 8.01783800e-01]])

        correct_cam2world_matrix = np.array([[-8.94427180e-01, -3.58568549e-01, 2.67261177e-01, 1.00000000e+00],
                                        [4.47213531e-01, -7.17137218e-01, 5.34522414e-01, 2.00000000e+00],
                                        [2.34371083e-08, 5.97614229e-01, 8.01783800e-01, 3.00000000e+00],
                                        [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])

        # Add homog cam pose based on location an rotation
        cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)

        for x, y in zip(np.reshape(correct_cam2world_matrix, -1).tolist(), np.reshape(cam2world_matrix, -1).tolist()):
            self.assertAlmostEqual(x, y)