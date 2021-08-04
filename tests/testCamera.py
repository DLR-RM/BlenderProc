import unittest
import os.path
import numpy as np
import bpy

from src.utility.CameraUtility import CameraUtility
from src.utility.Initializer import Initializer

resource_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources")

class UnitTestCheckCamera(unittest.TestCase):

    def test_camera_add_camera_pose(self):
        """ Tests if the camera to world matrix is set right.
        """
        Initializer.init()

        poi = np.array([0, 0, 0])
        #location = np.array([1, 2, 3])
        #rotation_matrix = np.array([[-0.5285266  -0.8057487   0.26726118]
                        # [ 0.7770431  -0.33239999  0.53452241]
                        # [-0.34185314  0.49018279  0.8017838 ]])
        cam2world_matrix = np.array([[-0.5285266, -0.8057487, 0.26726118, 1.0],
                                    [0.7770431, -0.33239999, 0.53452241, 2.0],
                                    [-0.34185314, 0.49018279, 0.8017838, 3.0],
                                    [0.0, 0.0, 0.0, 1.0]])
        CameraUtility.add_camera_pose(cam2world_matrix)

        cam_ob = bpy.context.scene.camera
        cam2world_matrix_calc = np.array(cam_ob.matrix_world)

        for x, y in zip(np.reshape(cam2world_matrix, -1).tolist(), np.reshape(cam2world_matrix_calc, -1).tolist()):
            self.assertAlmostEqual(x, y)
