import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.sampler.PartSphere import PartSphere
from blenderproc.python.types.LightUtility import Light

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/camera_depth_of_field/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# Create an empty object which will represent the cameras focus point
focus_point = Entity.create_empty("Camera Focus Point")
focus_point.set_location([0.5, -1.5, 3])

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
bproc.camera.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")
# Set the empty object as focus point and set fstop to regulate the sharpness of the scene
bproc.camera.add_depth_of_field(focus_point, fstop_value=0.25)

# Find point of interest, all cam poses should look towards it
poi = MeshObject.compute_poi(objs)
# Sample five camera poses
for i in range(5):
    # Sample random camera location above objects
    location = PartSphere.sample(center=[0, 0, 0], radius=7, mode="SURFACE", dist_above_center=1.0)
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)

# activate normal and distance rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
bproc.renderer.set_samples(350)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
