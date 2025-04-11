import blenderproc as bproc
import unittest
import os.path
import numpy as np
import bpy

resource_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources")

class UnitTestCheckCameraProjection(unittest.TestCase):

    def test_unproject_project(self):
        """ Test if unproject + project results in same coordinates.
        """
        bproc.clean_up(True)
        resource_folder = os.path.join("examples", "resources")
        objs = bproc.loader.load_obj(os.path.join(resource_folder, "scene.obj"))

        cam2world_matrix = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.2674988806247711, -0.9635581970214844, -13.741], [-0.0, 0.9635581970214844, 0.2674988806247711, 4.1242], [0.0, 0.0, 0.0, 1.0]])
        bproc.camera.add_camera_pose(cam2world_matrix)
        bproc.camera.set_resolution(640, 480)

        bvh_tree = bproc.object.create_bvh_tree_multi_objects(objs)

        depth = bproc.camera.depth_via_raytracing(bvh_tree)
        pc = bproc.camera.pointcloud_from_depth(depth)

        pixels = bproc.camera.project_points(pc.reshape(-1, 3)).reshape(480, 640, 2)

        y = np.arange(480)   
        x = np.arange(640)
        pixels_gt = np.stack(np.meshgrid(x, y), -1).astype(np.float32)
        pixels_gt[np.isnan(pixels[..., 0])] = np.nan

        np.testing.assert_almost_equal(pixels, pixels_gt, decimal=3)


    def test_depth_at_points_via_raytracing(self):
        """ Test if depth_at_points_via_raytracing leads to the same results as depth_via_raytracing + unproject + project
        """
        bproc.clean_up(True)
        resource_folder = os.path.join("examples", "resources")
        objs = bproc.loader.load_obj(os.path.join(resource_folder, "scene.obj"))

        cam2world_matrix = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.2674988806247711, -0.9635581970214844, -13.741], [-0.0, 0.9635581970214844, 0.2674988806247711, 4.1242], [0.0, 0.0, 0.0, 1.0]])
        bproc.camera.add_camera_pose(cam2world_matrix)
        bproc.camera.set_resolution(640, 480)

        bvh_tree = bproc.object.create_bvh_tree_multi_objects(objs)

        depth = bproc.camera.depth_via_raytracing(bvh_tree)
        pc = bproc.camera.pointcloud_from_depth(depth)
        pixels = bproc.camera.project_points(pc.reshape(-1, 3))
        
        depth2 = bproc.camera.depth_at_points_via_raytracing(bvh_tree, pixels)
        depth2[np.isnan(depth2)] = np.inf
        pc2 = bproc.camera.unproject_points(pixels, depth2)

        np.testing.assert_almost_equal(depth.flatten(), depth2, decimal=3)
        np.testing.assert_almost_equal(pc.reshape(-1, 3), pc2, decimal=3)


    def test_depth_via_raytracing(self):
        """ Tests if depth image via raytracing and rendered depth image are identical.
        """
        bproc.clean_up(True)
        resource_folder = os.path.join("examples", "resources")
        objs = bproc.loader.load_obj(os.path.join(resource_folder, "scene.obj"))


        cam2world_matrix = np.array([
            [1.0, 0.0, 0.0, 0.0], 
            [0.0, 0.2674988806247711, -0.9635581970214844, -13.741],
            [-0.0, 0.9635581970214844, 0.2674988806247711, 4.1242],
            [0.0, 0.0, 0.0, 1.0]
        ])
        bproc.camera.add_camera_pose(cam2world_matrix)
        bproc.camera.set_resolution(640, 480)

        bvh_tree = bproc.object.create_bvh_tree_multi_objects(objs)

        depth = bproc.camera.depth_via_raytracing(bvh_tree)

        bproc.renderer.enable_depth_output(activate_antialiasing=False)
        data = bproc.renderer.render()      
        data["depth"][0][data["depth"][0] >= 65504] = np.inf

        diff = np.abs(depth[~np.isinf(depth)] - data["depth"][0][~np.isinf(depth)])
        self.assertTrue(np.median(diff) < 1e-4)
        self.assertTrue((diff < 1e-4).mean() > 0.99)

if __name__ == '__main__':
    bproc.init()
    #test = UnitTestCheckCameraProjection()
    #test.test_depth_via_raytracing()
    unittest.main()
