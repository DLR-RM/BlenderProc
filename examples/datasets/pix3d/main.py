import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.sampler.Sphere import Sphere
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.types.LightUtility import Light

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('pix_path', help="Path to the downloaded pix3d dataset, see the [scripts folder](../../scripts) for the download script")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/pix3d/output", help="Path to the output directory")
args = parser.parse_args()

bproc.init()

# Load Pix3D objects from type table into the scene
objs = bproc.loader.load_pix3d(data_path=args.pix_path, used_category="bed")

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
    location = Sphere.sample([0, 0, 0], radius=2, mode="SURFACE")
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
