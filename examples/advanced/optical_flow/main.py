import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.utility.MathUtility import MathUtility

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('camera', nargs='?', default="examples/advanced/optical_flow/camera_positions", help="Path to the camera file")
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/optical_flow/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
bproc.camera.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position, euler_rotation = line[:3], line[3:6]
        matrix_world = bproc.math.build_transformation_mat(position, euler_rotation)
        bproc.camera.add_camera_pose(matrix_world)

# render the whole pipeline
data = bproc.renderer.render()

# Render the optical flow (forward and backward) for all frames
data.update(bproc.renderer.render_optical_flow(get_backward_flow=True, get_forward_flow=True, blender_image_coordinate_style=False))

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
