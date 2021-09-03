from blenderproc.python.SetupUtility import SetupUtility
SetupUtility.setup([])

import argparse

from blenderproc.python.Utility import Utility
from blenderproc.python.sampler.Shell import Shell
from blenderproc.python.WriterUtility import WriterUtility
from blenderproc.python.Initializer import Initializer
from blenderproc.python.loader.ObjectLoader import ObjectLoader
from blenderproc.python.CameraUtility import CameraUtility
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.MathUtility import MathUtility
from blenderproc.python.RendererUtility import RendererUtility

parser = argparse.ArgumentParser()
parser.add_argument('camera', nargs='?', default="examples/resources/scene.obj", help="Path to the camera file")
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/basics/light_sampling/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
objs = ObjectLoader.load(args.scene)

# Define a light
light = Light()
light.set_type("POINT")
# Sample its location in a shell around the point [1, 2, 3]
light.set_location(Shell.sample(
    center=[1, 2, 3],
    radius_min=4,
    radius_max=7,
    elevation_min=15,
    elevation_max=70
))
light.set_energy(500)

# define the camera intrinsics
CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position, euler_rotation = line[:3], line[3:6]
        matrix_world = MathUtility.build_transformation_mat(position, euler_rotation)
        CameraUtility.add_camera_pose(matrix_world)

# render the whole pipeline
data = RendererUtility.render()

# Collect states of all objects
object_states = []
for obj in objs:
    object_states.append({
        "name": obj.get_name(),
        "local2world": obj.get_local2world_mat()
    })
# Add states (they are the same for all frames here)
data["object_states"] = [object_states] * Utility.num_frames()

# Collect state of the one light
light_state = {
    "name": light.get_name(),
    "local2world": light.get_local2world_mat(),
    "energy": light.get_energy()
}
# Add states (its the same for all frames here)
data["light_states"] = [light_state] * Utility.num_frames()

# Collect state of the camera at all frames
cam_states = []
for frame in range(Utility.num_frames()):
    cam_states.append({
        "cam2world": CameraUtility.get_camera_pose(frame),
        "cam_K": CameraUtility.get_intrinsics_as_K_matrix()
    })
# Adds states to the data dict
data["cam_states"] = cam_states

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
