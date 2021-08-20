from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

import argparse
import numpy as np

from src.utility.BopWriterUtility import BopWriterUtility
from src.utility.Initializer import Initializer
from src.utility.loader.ObjectLoader import ObjectLoader
from src.utility.CameraUtility import CameraUtility
from src.utility.LightUtility import Light
from src.utility.MathUtility import MathUtility

from src.utility.RendererUtility import RendererUtility
from src.utility.PostProcessingUtility import PostProcessingUtility


parser = argparse.ArgumentParser()
parser.add_argument('object', nargs='?', default="examples/basics/camera_object_pose/obj_000004.ply", help="Path to the model file")
parser.add_argument('output_dir', nargs='?', default="examples/basics/camera_object_pose/output", help="Path to where the final files will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
obj = ObjectLoader.load(args.object)[0]
# Use vertex color for texturing
for mat in obj.get_materials():
    mat.map_vertex_color()
# Set pose of object via local-to-world transformation matrix
obj.set_local2world_mat(
    [[0.331458, -0.9415833, 0.05963787, -0.04474526765165741],
    [-0.6064861, -0.2610635, -0.7510136, 0.08970402424862098],
    [0.7227108, 0.2127592, -0.6575879, 0.6823395750305427],
    [0, 0, 0, 1.0]]
)
# Scale 3D model from mm to m
obj.set_scale([0.001, 0.001, 0.001])
# Set category id which will be used in the BopWriter
obj.set_cp("category_id", 1)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Set intrinsics via K matrix
CameraUtility.set_intrinsics_from_K_matrix(
    [[537.4799, 0.0, 318.8965],
     [0.0, 536.1447, 238.3781],
     [0.0, 0.0, 1.0]], 640, 480
)
# Set camera pose via cam-to-world transformation matrix
cam2world = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
])
# Change coordinate frame of transformation matrix from OpenCV to Blender coordinates
cam2world = MathUtility.change_source_coordinate_frame_of_transformation_matrix(cam2world, ["X", "-Y", "-Z"])
CameraUtility.add_camera_pose(cam2world)

# activate normal and distance rendering
RendererUtility.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(100)

# render the whole pipeline
data = RendererUtility.render()

# Map distance to depth
depth = PostProcessingUtility.dist2depth(data["distance"])

# Write object poses, color and depth in bop format
BopWriterUtility.write(args.output_dir, depth, data["colors"], m2mm=True, append_to_existing_output=True)