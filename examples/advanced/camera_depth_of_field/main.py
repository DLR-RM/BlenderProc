from blenderproc.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.utility.EntityUtility import Entity
from blenderproc.utility.MeshObjectUtility import MeshObject
from blenderproc.utility.sampler.PartSphere import PartSphere
from blenderproc.utility.WriterUtility import WriterUtility
from blenderproc.utility.Initializer import Initializer
from blenderproc.utility.CameraUtility import CameraUtility
from blenderproc.utility.LightUtility import Light
from blenderproc.utility.MathUtility import MathUtility
from blenderproc.utility.loader.ObjectLoader import ObjectLoader
from blenderproc.utility.RendererUtility import RendererUtility

import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/camera_depth_of_field/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
objs = ObjectLoader.load(args.scene)

# Create an empty object which will represent the cameras focus point
focus_point = Entity.create_empty("Camera Focus Point")
focus_point.set_location([0.5, -1.5, 3])

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")
# Set the empty object as focus point and set fstop to regulate the sharpness of the scene
CameraUtility.add_depth_of_field(focus_point, fstop_value=0.25)

# Find point of interest, all cam poses should look towards it
poi = MeshObject.compute_poi(objs)
# Sample five camera poses
for i in range(5):
    # Sample random camera location above objects
    location = PartSphere.sample(center=[0, 0, 0], radius=7, mode="SURFACE", dist_above_center=1.0)
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
