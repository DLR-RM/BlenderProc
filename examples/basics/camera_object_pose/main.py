import blenderproc as bproc
import argparse
import numpy as np



parser = argparse.ArgumentParser()
parser.add_argument('object', nargs='?', default="examples/basics/camera_object_pose/obj_000004.ply", help="Path to the model file")
parser.add_argument('output_dir', nargs='?', default="examples/basics/camera_object_pose/output", help="Path to where the final files will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
obj = bproc.loader.load_obj(args.object)[0]
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
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Set intrinsics via K matrix
bproc.camera.set_intrinsics_from_K_matrix(
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
cam2world = bproc.math.change_source_coordinate_frame_of_transformation_matrix(cam2world, ["X", "-Y", "-Z"])
bproc.camera.add_camera_pose(cam2world)

# activate depth rendering
bproc.renderer.enable_depth_output(activate_antialiasing=False)

# render the whole pipeline
data = bproc.renderer.render()

# Write object poses, color and depth in bop format
bproc.writer.write_bop(args.output_dir, [obj], data["depth"], data["colors"], m2mm=True, append_to_existing_output=True)
