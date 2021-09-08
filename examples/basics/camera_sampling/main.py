import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.camera.CameraUtility import CameraUtility
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.types.LightUtility import Light

from blenderproc.python.renderer.RendererUtility import RendererUtility

import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/basics/camera_sampling/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Find point of interest, all cam poses should look towards it
poi = MeshObject.compute_poi(objs)
# Sample five camera poses
for i in range(5):
    # Sample random camera location above objects
    location = np.random.uniform([-10, -10, 12], [10, 10, 8])
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = CameraUtility.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
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
