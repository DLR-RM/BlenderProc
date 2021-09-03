from blenderproc.python.SetupUtility import SetupUtility
SetupUtility.setup([])

import argparse

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.object.ObjectPoseSampler import ObjectPoseSampler
from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.Initializer import Initializer
from blenderproc.python.loader.ObjectLoader import ObjectLoader
from blenderproc.python.CameraUtility import CameraUtility
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.MathUtility import MathUtility

from blenderproc.python.RendererUtility import RendererUtility
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('camera', nargs='?', default="examples/resources/camera_positions", help="Path to the camera file")
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/object_pose_sampling/output", help="Path to where the final files will be saved ")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
objs = ObjectLoader.load(args.scene)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position, euler_rotation = line[:3], line[3:6]
        matrix_world = MathUtility.build_transformation_mat(position, euler_rotation)
        CameraUtility.add_camera_pose(matrix_world)

# Define a function that samples the pose of a given object
def sample_pose(obj: MeshObject):
    obj.set_location(np.random.uniform([-5, -5, -5], [5, 5, 5]))
    obj.set_rotation_euler(np.random.uniform([0, 0, 0], [np.pi * 2, np.pi * 2, np.pi * 2]))

# Sample the poses of all objects, while making sure that no objects collide with each other.
ObjectPoseSampler.sample(
    objs,
    sample_pose_func=sample_pose,
    objects_to_check_collisions=objs
)

# activate normal rendering
RendererUtility.enable_normals_output()
# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(50)

# render the whole pipeline
data = RendererUtility.render()

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
