from blenderproc.python.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.loader.BlendLoader import BlendLoader
from blenderproc.python.loader.HavenEnvironmentLoader import HavenEnvironmentLoader
from blenderproc.python.materials.Dust import Dust
from blenderproc.python.sampler.PartSphere import PartSphere

from blenderproc.python.MathUtility import MathUtility
from blenderproc.python.CameraUtility import CameraUtility
from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.Initializer import Initializer
from blenderproc.python.types.LightUtility import Light

from blenderproc.python.renderer.RendererUtility import RendererUtility

import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('model', nargs='?', default="resources/haven/models/ArmChair_01/ArmChair_01_2k.blend", help="ath to the blend file, from the haven dataset, browse the model folder, for all possible options")
parser.add_argument('hdri_path', nargs='?', default="resources/haven", help="The folder where the `hdri` folder can be found, to load an world environment")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/haven/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
obj = BlendLoader.load(args.model)[0]

HavenEnvironmentLoader.set_random_world_background_hdr_img(args.hdri_path)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Sample five camera poses
for i in range(5):
    # Sample random camera location above objects
    location = PartSphere.sample(center=np.array([0, 0, 0]), mode="SURFACE", radius=3, part_sphere_dir_vector=np.array([1, 0, 0]), dist_above_center=0.5)
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = CameraUtility.rotation_from_forward_vec(obj.get_location() - location)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = MathUtility.build_transformation_mat(location, rotation_matrix)
    CameraUtility.add_camera_pose(cam2world_matrix)

# Add dust to all materials of the loaded object
for material in obj.get_materials():
    Dust.add_to_material(material, strength=0.8, texture_scale=0.05)

# activate normal and distance rendering
RendererUtility.enable_normals_output()
RendererUtility.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(350)

# render the whole pipeline
data = RendererUtility.render()

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
