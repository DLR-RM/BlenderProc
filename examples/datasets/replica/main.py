import blenderproc as bproc
import argparse
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("replica_data_folder", help="Path to the replica dataset directory.")
parser.add_argument("output_dir", help="Path to where the data should be saved")
args = parser.parse_args()

# Define which dataset should be loaded and the path to the file containing possible height values.
data_set_name = "office_1"
height_list_values = bproc.utility.resolve_resource(os.path.join('replica', 'height_levels', data_set_name, 'height_list_values.txt'))

bproc.init()

# Load the replica dataset
objs = bproc.loader.load_replica(args.replica_data_folder, data_set_name, use_smooth_shading=True)
# Extract the floor from the loaded room
floor = bproc.object.extract_floor(objs, new_name_for_object="floor")[0]
room = bproc.filter.one_by_attr(objs, "name", "mesh")

# Init sampler for sampling locations inside the loaded replica room
point_sampler = bproc.sampler.ReplicaPointInRoomSampler(room, floor, height_list_values)

# define the camera intrinsics
bproc.camera.set_resolution(512, 512)

# Init bvh tree containing all mesh objects
bvh_tree = bproc.object.create_bvh_tree_multi_objects([room, floor])

poses = 0
tries = 0
while tries < 10000 and poses < 15:
    # Sample point inside room at 1.55m height
    location = point_sampler.sample(height=1.55)
    # Sample rotation (fix around X and Y axis)
    rotation = np.random.uniform([1.373401334, 0, 0], [1.373401334, 0, 2 * np.pi])
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation)

    # Check that obstacles are at least 1 meter away from the camera and have an average distance between 2 and 4 meters
    if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0, "avg": {"min": 2.0, "max": 4.0}}, bvh_tree):
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# Use vertex color of mesh as texture for all materials
for mat in room.get_materials():
    mat.map_vertex_color("Col", active_shading=False)

# Activate normal rendering
bproc.renderer.enable_normals_output()

# Render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
