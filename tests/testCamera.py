import blenderproc as bproc
import unittest
import os.path
import numpy as np
import bpy

resource_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources")

class UnitTestCheckCamera(unittest.TestCase):

    def test_camera_add_camera_pose(self):
        """ Tests if the camera to world matrix is set right.
        """
        bproc.clean_up(True)

        poi = np.array([0, 0, 0])
        #location = np.array([1, 2, 3])
        #rotation_matrix = np.array([[-0.5285266  -0.8057487   0.26726118]
                        # [ 0.7770431  -0.33239999  0.53452241]
                        # [-0.34185314  0.49018279  0.8017838 ]])
        cam2world_matrix = np.array([[-0.5285266, -0.8057487, 0.26726118, 1.0],
                                    [0.7770431, -0.33239999, 0.53452241, 2.0],
                                    [-0.34185314, 0.49018279, 0.8017838, 3.0],
                                    [0.0, 0.0, 0.0, 1.0]])
        bproc.camera.add_camera_pose(cam2world_matrix)

        cam_ob = bpy.context.scene.camera
        cam2world_matrix_calc = np.array(cam_ob.matrix_world)

        for x, y in zip(np.reshape(cam2world_matrix, -1).tolist(), np.reshape(cam2world_matrix_calc, -1).tolist()):
            self.assertAlmostEqual(x, y)

    def test_camera_rotation_from_forward_vec(self):
        """ Tests if the camera rotation from forward vec is calculated right.
        """
        poi = np.array([0, 0, 0])
        location = np.array([1, 2, 3])
        rotation = 0.0
        # correct_rotation_matrix
        correct_roation_matrix = np.array([[-8.94427180e-01, -3.58568549e-01, 2.67261177e-01],
                                            [ 4.47213531e-01, -7.17137218e-01, 5.34522414e-01],
                                            [ 2.34371083e-08,  5.97614229e-01, 8.01783800e-01]])

        # Compute rotation based on vector going from location towards poi
        calc_rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=rotation)

        for x, y in zip(np.reshape(correct_roation_matrix, -1).tolist(), np.reshape(calc_rotation_matrix, -1).tolist()):
            self.assertAlmostEqual(x, y, places=6)

