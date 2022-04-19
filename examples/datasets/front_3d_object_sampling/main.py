import blenderproc as bproc

import numpy as np
import argparse
import bpy

from blenderproc.python.utility.CollisionUtility import CollisionUtility
parser = argparse.ArgumentParser()
parser.add_argument('output_dir', nargs='?', default="examples/datasets/shapenet_with_scenenet/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# define the camera intrinsics
bproc.camera.set_resolution(512, 512)

# Path to front-3D scene
threeD_scene_path = "/home/markus/workspace/BlenderProc/blenderproc/resources/3D_future_scenes/3D_future_scene_036bc96c-419d-4a43-812e-1e533d95dfd3.blend"

room_objs = bproc.loader.load_blend(threeD_scene_path)

left_objects = []

for obj in room_objs:
    if "wall" in obj.get_name().lower():
        obj.delete()
        continue
    elif "ceiling" in obj.get_name().lower():
        obj.delete()
        continue
    left_objects.append(obj)
for obj in left_objects:
    if "table" in obj.get_name().lower() or "desk" in obj.get_name().lower():
        with bproc.python.utility.Utility.Utility.UndoAfterExecution():
            droppable_surface = bproc.object.slice_faces_with_normals([obj])
            if droppable_surface is not None and len(droppable_surface) == 1:
                surface_obj = droppable_surface[0]
            else:
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
                obj.set_rotation_euler(np.random.uniform([0, 0, 0], [np.pi * 2, np.pi * 2, np.pi * 2]))


            sampling_obj = bproc.loader.load_blend(
                "/home/markus/workspace/BlenderProc/examples/advanced/on_surface_object_sampling/apple.blend")
            dropped_object_list = bproc.object.sample_poses_on_surface(sampling_obj, surface_obj, sample_pose,
                                                                       min_distance=0.1, max_distance=10)

            # dropped_objects.append(dropped_object_list)
            # Enable physics for spheres (active) and the surface (passive)
            for dropped_object in dropped_object_list:
                dropped_object.enable_rigidbody(True)
            surface_obj.enable_rigidbody(False)

            # Run the physics simulation
            bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=2, max_simulation_time=4,
                                                              check_object_interval=1)

            def conv_to_homogen(x):
                x = x.co.to_4d()
                x[3] = 1.0
                return x

            # join surface objects again
            bpy.ops.object.select_all(action='DESELECT')
            obj.select()
            surface_obj.select()
            bpy.context.view_layer.objects.active = surface_obj.blender_obj
            bpy.ops.object.join()
            bpy.ops.object.select_all(action='DESELECT')

            min_coord_z = np.min([dropped_object.get_local2world_mat() @ conv_to_homogen(vert) for vert in
                                  dropped_object.blender_obj.data.vertices], axis=0)[2]

            # Check if object is on surface, otherwise delete object
            remove_list = []
            for index, dropped_object in enumerate(dropped_object_list):
                # if distance is smaller than 5 cm
                if abs(min_coord_z - surface_height_z) > 0.05:
                    dropped_object.delete()
                    remove_list.append(index)

            # remove deleted elements from dropped object list
            for ele in remove_list[::-1]:
                del dropped_object_list[ele]

            if not dropped_object_list:
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
            bvh_tree = bproc.object.create_bvh_tree_multi_objects([o for o in bproc.object.get_all_mesh_objects()])
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

            data = bproc.renderer.render()

            # write the data to a .hdf5 container
            bproc.writer.write_hdf5(args.output_dir, data, append_to_existing_output=True)
