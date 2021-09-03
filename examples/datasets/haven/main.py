from blenderproc.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.utility.loader.BlendLoader import BlendLoader
from blenderproc.utility.loader.HavenEnvironmentLoader import HavenEnvironmentLoader
from blenderproc.utility.sampler.PartSphere import PartSphere
from blenderproc.utility.MathUtility import MathUtility
from blenderproc.utility.CameraUtility import CameraUtility
from blenderproc.utility.MeshObjectUtility import MeshObject
from blenderproc.utility.WriterUtility import WriterUtility
from blenderproc.utility.Initializer import Initializer
from blenderproc.utility.LightUtility import Light
from blenderproc.utility.RendererUtility import RendererUtility

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('blend_path', nargs='?', default="resources/haven/models/ArmChair_01/ArmChair_01.blend", help="Path to the blend file, from the haven dataset, browse the model folder, for all possible options")
parser.add_argument('haven_path', nargs='?', default="resources/haven", help="The folder where the `hdri` folder can be found, to load an world environment")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/haven/output", help="Path to where the final files will be saved")
args = parser.parse_args()

Initializer.init()

# Load the object into the scene
objs = BlendLoader.load(args.blend_path)

# Set a random hdri from the given haven directory as background
HavenEnvironmentLoader.set_random_world_background_hdr_img(args.haven_path)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Find point of interest, all cam poses should look towards it
poi = MeshObject.compute_poi(objs)
# Sample five camera poses
for i in range(5):
    # Sample random camera location around the object
    location = PartSphere.sample([0, 0, 0], radius=3, part_sphere_dir_vector=[1, 0, 0], mode="SURFACE")
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = CameraUtility.rotation_from_forward_vec(poi - location)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = MathUtility.build_transformation_mat(location, rotation_matrix)
    CameraUtility.add_camera_pose(cam2world_matrix)

# activate normal and distance rendering
RendererUtility.enable_normals_output()
RendererUtility.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(350)

# render the whole pipeline
data = RendererUtility.render()

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
