import blenderproc as bproc
import argparse
import numpy as np

from blenderproc.python.utility.Utility import Utility

parser = argparse.ArgumentParser()
parser.add_argument('camera', nargs='?', default="examples/resources/camera_positions", help="Path to the camera file")
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.blend file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/point_clouds/output", help="Path to where the final files will be saved ")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera resolution
bproc.camera.set_resolution(128, 128)
bvh_tree = bproc.object.create_bvh_tree_multi_objects(objs)
# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position, euler_rotation = line[:3], line[3:6]
        matrix_world = bproc.math.build_transformation_mat(position, euler_rotation)
        bproc.camera.add_camera_pose(matrix_world)
        
# Compute a depth image from the view of the second camera pose
depth = bproc.camera.depth_via_raytracing(bvh_tree, 1)

# Project the depth again to get a point cloud
points = bproc.camera.pointcloud_from_depth(depth, 1)
points = points.reshape(-1, 3)

# Visualize the points cloud as a mesh
point_cloud = bproc.object.create_from_point_cloud(points, "point_cloud", add_geometry_nodes_visualization=True)

# render the whole pipeline
bproc.camera.set_resolution(512, 512)
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)

