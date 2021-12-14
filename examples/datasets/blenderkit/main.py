import blenderproc as bproc
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('path', help="Path to the downloaded .blend file")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/blenderkit/output", help="Path to where the final files will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_blend(args.path)

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Find point of interest, all cam poses should look towards it
poi = bproc.object.compute_poi(bproc.filter.all_with_type(objs, bproc.types.MeshObject))

# Sample five camera poses
for i in range(5):
    # Sample random camera location around the objects
    location = bproc.sampler.part_sphere([0, 0, 0], radius=2.5, part_sphere_dir_vector=[1, 0, 0], mode="SURFACE")
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
