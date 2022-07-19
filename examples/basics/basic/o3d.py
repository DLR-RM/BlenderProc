import numpy as np
import open3d as o3d


mesh = o3d.io.read_triangle_mesh("examples/basics/basic/texturedMesh.obj")

pose_inv = np.array(
    [
        [-0.2044, 0.2847, -0.9366, 321.3],
        [0.9788, 0.0737, -0.1912, 105.8],
        [0.0146, -0.9558, -0.2937, 86.6],
        [0, 0, 0, 1]
    ]
)

cam_intrinsic = o3d.camera.PinholeCameraIntrinsic()
cam_intrinsic.set_intrinsics(
    width=1920,
    height=1080,
    fx=1614.5,
    cx=968.5,
    fy=1620.6,
    cy=546
)
camparam = o3d.camera.PinholeCameraParameters()
camparam.extrinsic = pose_inv
camparam.intrinsic = cam_intrinsic
visualizer = o3d.visualization.Visualizer()
visualizer.create_window(window_name="Open3D", width=1920, height=1080, left=50, top=50)

ctr = visualizer.get_view_control()

ctr.convert_from_pinhole_camera_parameters(camparam, True)
visualizer.run()