from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

import argparse
import os

import numpy as np
import bpy

from src.utility.WriterUtility import WriterUtility
from src.utility.Initializer import Initializer
from src.utility.loader.ObjectLoader import ObjectLoader
from src.utility.CameraUtility import CameraUtility
from src.utility.LightUtility import Light
from src.utility.MathUtility import MathUtility
from src.utility.MeshObjectUtility import MeshObject

from src.utility.RendererUtility import RendererUtility
from src.utility.PostProcessingUtility import PostProcessingUtility

parser = argparse.ArgumentParser()
parser.add_argument('scene', help="Path to the scene.obj file, should be examples/resources/scene.obj")
parser.add_argument('output_dir', help="Path to where the final files, will be saved, could be examples/basics/basic/output")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
objs = ObjectLoader.load(args.scene)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# set the camera intrinsics
resolution_x, resolution_y = 640, 480
cam_K = np.array([[349.554, 0.0, 336.84], [0.0, 349.554, 189.185], [0.0, 0.0, 1.0]])
k1, k2, k3 = -0.172992, 0.0248708, 0.00149384
p1, p2 = 0.000311976, -9.62967e-5

# reuse the values, which have been set before
clip_start = bpy.context.scene.camera.data.clip_start
clip_end = bpy.context.scene.camera.data.clip_end

CameraUtility.set_intrinsics_from_K_matrix(cam_K, resolution_x, resolution_y, clip_start, clip_end)

# apply the lens distortion, this only adds the necessary mapping to GlobalStorage, so that it can be later used
# in the PostProcessing
CameraUtility.set_lens_distortion(k1, k2, k3, p1, p2)

# Find point of interest, all cam poses should look towards it
poi = MeshObject.compute_poi(objs)
# Sample five camera poses
for i in range(2):
    # Sample random camera location above objects
    location = np.random.uniform([-10, -10, 12], [10, 10, 8])
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = CameraUtility.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
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

# post process the data and apply the lens distortion
for key in data.keys():
    # make sure the input is only an image
    if isinstance(data[key], list) and len(data[key][0].shape) >= 2:
        data[key] = PostProcessingUtility.apply_lens_distortion(data[key])

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
