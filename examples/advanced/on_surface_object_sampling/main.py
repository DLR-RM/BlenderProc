from blenderproc.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

import argparse
import numpy as np

from blenderproc.utility.object.PhysicsSimulation import PhysicsSimulation
from blenderproc.utility.WriterUtility import WriterUtility
from blenderproc.utility.Initializer import Initializer
from blenderproc.utility.loader.BlendLoader import BlendLoader
from blenderproc.utility.CameraUtility import CameraUtility
from blenderproc.utility.LightUtility import Light
from blenderproc.utility.MathUtility import MathUtility
from blenderproc.utility.MeshObjectUtility import MeshObject
from blenderproc.utility.filter.Filter import Filter
from blenderproc.utility.object.OnSurfaceSampler import OnSurfaceSampler
from blenderproc.utility.sampler.UpperRegionSampler import UpperRegionSampler

from blenderproc.utility.RendererUtility import RendererUtility

parser = argparse.ArgumentParser()
parser.add_argument('camera', nargs='?', default="examples/resources/camera_positions", help="Path to the camera file")
parser.add_argument('scene', nargs='?', default="examples/advanced/on_surface_object_sampling/scene.blend", help="Path to the scene.blend file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/on_surface_object_sampling/output", help="Path to where the final files will be saved ")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
objs = BlendLoader.load(args.scene)

# Retrieve surface and spheres from the list objects
surface = Filter.one_by_attr(objs, "name", "Cube")
spheres = Filter.by_attr(objs, "name", ".*phere.*", regex=True)

# Define a function that samples the pose of a given object
def sample_pose(obj: MeshObject):
    # Sample the spheres location above the surface
    obj.set_location(UpperRegionSampler.sample(
        objects_to_sample_on=[surface],
        min_height=1,
        max_height=4,
        use_ray_trace_check=False
    ))
    obj.set_rotation_euler(np.random.uniform([0, 0, 0], [np.pi * 2, np.pi * 2, np.pi * 2]))

# Sample the spheres on the surface
spheres = OnSurfaceSampler.sample(spheres, surface, sample_pose, min_distance=0.1, max_distance=10)

# Enable physics for spheres (active) and the surface (passive)
for sphere in spheres:
    sphere.enable_rigidbody(True)
surface.enable_rigidbody(False)

# Run the physics simulation
PhysicsSimulation.simulate_and_fix_final_poses(min_simulation_time=2, max_simulation_time=4, check_object_interval=1)

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

# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(350)

# render the whole pipeline
data = RendererUtility.render()

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
