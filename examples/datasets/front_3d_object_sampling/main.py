import blenderproc as bproc
import os
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("front", help="Path to the 3D front file")
parser.add_argument("future_folder", help="Path to the 3D Future Model folder.")
parser.add_argument("front_3D_texture_path", help="Path to the 3D FRONT texture folder.")
parser.add_argument('treed_obj_path', help="Path to the downloaded 3D object")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/front_3d_object_sampling/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

if not os.path.exists(args.front) or not os.path.exists(args.future_folder) or not os.path.exists(args.treed_obj_path):
    raise OSError("One of the three folders does not exist!")

bproc.init()
mapping_file = bproc.utility.resolve_resource(os.path.join("front_3D", "3D_front_mapping.csv"))
mapping = bproc.utility.LabelIdMapping.from_csv(mapping_file)

# set the light bounces
bproc.renderer.set_light_bounces(diffuse_bounces=200, glossy_bounces=200, max_bounces=200,
                                  transmission_bounces=200, transparent_max_bounces=200)

# load the front 3D objects
room_objs = bproc.loader.load_front3d(
    json_path=args.front,
    future_model_path=args.future_folder,
    front_3D_texture_path=args.front_3D_texture_path,
    label_mapping=mapping
)

# define the camera intrinsics
bproc.camera.set_resolution(512, 512)

# Select the objects, where other objects should be sampled on
sample_surface_objects = []
for obj in room_objs:
    if "table" in obj.get_name().lower() or "desk" in obj.get_name().lower():
        sample_surface_objects.append(obj)

for obj in sample_surface_objects:
    # The loop starts with and UndoAfterExecution in order to clean up the cam poses from the previous iteration and
    # also remove the dropped objects and restore the sliced up objects.
    with bproc.utility.UndoAfterExecution():
        # Select the surfaces, where the object should be sampled on
        surface_obj = bproc.object.slice_faces_with_normals(obj)
        if surface_obj is None:
            continue

        surface_height_z = np.mean(surface_obj.get_bound_box(), axis=0)[2]
        def sample_pose(obj: bproc.types.MeshObject):
            # Sample the spheres location above the surface
            obj.set_location(bproc.sampler.upper_region(
                objects_to_sample_on=[surface_obj],
                min_height=1,
                max_height=4,
                use_ray_trace_check=False
            ))
            #Randomized rotation of the sampled object
            obj.set_rotation_euler(bproc.sampler.uniformSO3())

        # Load the object, which should be sampled on the surface
        sampling_obj = bproc.loader.load_blend(args.treed_obj_path)
        dropped_object_list = bproc.object.sample_poses_on_surface(sampling_obj, surface_obj, sample_pose,
                                                                   min_distance=0.1, max_distance=10,
                                                                   check_all_bb_corners_over_surface=False)
        if not dropped_object_list:
            print("Dropping of the object failed")
            continue

        # Enable physics for spheres (active) and the surface (passive)
        for dropped_object in dropped_object_list:
            dropped_object.enable_rigidbody(True)
        surface_obj.enable_rigidbody(False)

        # Run the physics simulation
        bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=2, max_simulation_time=4,
                                                          check_object_interval=1)

        # join surface objects again
        surface_obj.join_with_other_objects([obj])

        # get the minimum value of all eight corners and from that the Z value
        min_coord_z = np.min(dropped_object.get_bound_box(local_coords=False), axis=0)[2]

        # Check if object is on surface, otherwise delete object
        remove_list = []
        for index, dropped_object in enumerate(dropped_object_list):
            # if distance is smaller than 5 cm
            print(f"Object: {dropped_object.get_name()} has a diff of: {abs(min_coord_z - surface_height_z)}m to the surface")
            if abs(min_coord_z - surface_height_z) > 0.05:
                print("Delete this object, distance is above 0.05m")
                dropped_object.delete()
                remove_list.append(index)

        # remove deleted elements from dropped object list
        for ele in remove_list[::-1]:
            del dropped_object_list[ele]

        if not dropped_object_list:
            print(f"List is empty after removal of objects")
            # skip if no object is left
            continue

        # place a camera
        object_location = np.mean(dropped_object.get_bound_box(), axis=0)
        object_size = np.max(np.max(dropped_object.get_bound_box(), axis=0) - np.min(dropped_object.get_bound_box(), axis=0))
        radius_min = object_size * 1.5
        radius_max = object_size * 10

        proximity_checks = {"min": radius_min, "avg": {"min": radius_min * 1.2, "max": radius_max * 0.8}, "no_background": True}
        cam_counter = 0
        # Init bvh tree containing all mesh objects
        bvh_tree = bproc.object.create_bvh_tree_multi_objects(bproc.object.get_all_mesh_objects())
        for i in range(1000):
            camera_location = bproc.sampler.shell(center=object_location, radius_min=radius_min, radius_max=radius_max,
                                                  elevation_min=15, elevation_max=70)

            # Make sure that object is not always in the center of the camera
            toward_direction = (object_location + np.random.uniform(0, 1, size=3) * object_size * 0.5) - camera_location

            # Compute rotation based on vector going from location towards poi
            rotation_matrix = bproc.camera.rotation_from_forward_vec(toward_direction, inplane_rot=np.random.uniform(-0.7854, 0.7854))
            # Add homog cam pose based on location an rotation
            cam2world_matrix = bproc.math.build_transformation_mat(camera_location, rotation_matrix)

            if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, proximity_checks, bvh_tree) \
                    and dropped_object in bproc.camera.visible_objects(cam2world_matrix, sqrt_number_of_rays=15):
                bproc.camera.add_camera_pose(cam2world_matrix)
                cam_counter += 1
            if cam_counter == 2:
                break
        if cam_counter == 0:
            raise Exception("No valid camera pose found!")

        data = bproc.renderer.render()

        # write the data to a .hdf5 container
        bproc.writer.write_hdf5(args.output_dir, data, append_to_existing_output=True)
