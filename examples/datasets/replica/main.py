import blenderproc as bproc
import argparse
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("replica_data_folder", help="Path to the replica dataset directory.")
parser.add_argument("--room_name", help="Name of the used room.", default="apartment_1")
parser.add_argument("output_dir", help="Path to where the data should be saved")
parser.add_argument("--load_segmented_objects", help="If this is given, the object is loaded as a segmented object.", default=False, action="store_true")
args = parser.parse_args()

# Define which dataset should be loaded and the path to the file containing possible height values.
data_set_name = args.room_name
if not os.path.exists(args.replica_data_folder):
    raise Exception("The given replica folder does not exist!")

if not os.path.exists(os.path.join(args.replica_data_folder, data_set_name)):
    raise Exception(f"The given room name \"{data_set_name}\" does not exist!")

height_list_values = bproc.utility.resolve_resource(os.path.join('replica', 'height_levels', data_set_name, 'height_list_values.txt'))

bproc.init()

# Load the replica dataset
if args.load_segmented_objects:
    objs = bproc.loader.load_replica_segmented_mesh(args.replica_data_folder, data_set_name, use_smooth_shading=True)
    floor = bproc.filter.by_attr(objs, "name", "floor")
else:
    objs = bproc.loader.load_replica(args.replica_data_folder, data_set_name, use_smooth_shading=True)
    # Extract the floor from the loaded room
    floor = bproc.object.extract_floor(objs, new_name_for_object="floor")[0]
    room = bproc.filter.one_by_attr(objs, "name", "mesh")

print("Loaded the replica file")

for obj in objs:
    if len(obj.get_materials()) == 0:
        obj.new_material("VertexColor")
    # Use vertex color of mesh as texture for all materials
    for mat in obj.get_materials():
        mat.map_vertex_color("Col", active_shading=False)

# Init sampler for sampling locations inside the loaded replica room
room_bounding_box = np.array([obj.get_bound_box() for obj in objs]).reshape((-1, 3))
room_bounding_box = {"min": np.min(room_bounding_box, axis=0), "max": np.max(room_bounding_box, axis=0)}
point_sampler = bproc.sampler.ReplicaPointInRoomSampler(room_bounding_box, floor, height_list_values)

# define the camera intrinsics
bproc.camera.set_resolution(512, 512)

# Init bvh tree containing all mesh objects
bvh_tree = bproc.object.create_bvh_tree_multi_objects(objs)

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

# Activate normal rendering
bproc.renderer.enable_normals_output()

# Render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
