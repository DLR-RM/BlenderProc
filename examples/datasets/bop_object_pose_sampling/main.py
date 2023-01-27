import blenderproc as bproc
import argparse
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('bop_parent_path', nargs='?', help="Path to the bop datasets parent directory")
parser.add_argument('bop_dataset_name', nargs='?', help="Main BOP dataset")
parser.add_argument('output_dir', nargs='?', help="Path to where the final files will be saved ")
args = parser.parse_args()

bproc.init()

# load specified bop objects into the scene
bop_objs = bproc.loader.load_bop_objs(bop_dataset_path=os.path.join(args.bop_parent_path, args.bop_dataset_name),
                                      mm2m=True,
                                      obj_ids=[1, 1, 3])

# load BOP datset intrinsics
bproc.loader.load_bop_intrinsics(bop_dataset_path=os.path.join(args.bop_parent_path, args.bop_dataset_name))

# set shading
for j, obj in enumerate(bop_objs):
    obj.set_shading_mode('auto')

# sample point light on shell
light_point = bproc.types.Light()
light_point.set_energy(500)
location = bproc.sampler.shell(center=[0, 0, -0.8], radius_min=1, radius_max=4,
                               elevation_min=40, elevation_max=89, uniform_volume=False)
light_point.set_location(location)


# Define a function that samples 6-DoF poses
def sample_pose_func(obj: bproc.types.MeshObject):
    obj.set_location(np.random.uniform([-0.2, -0.2, -0.2], [0.2, 0.2, 0.2]))
    obj.set_rotation_euler(bproc.sampler.uniformSO3())


# activate depth rendering
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.set_max_amount_of_samples(50)

# add segmentation masks (per class and per instance)
bproc.renderer.enable_segmentation_output(map_by=["category_id", "instance", "name", "bop_dataset_name"],
                                          default_values={"category_id": 0, "bop_dataset_name": None})

# Render five different scenes
for _ in range(5):

    # Sample object poses and check collisions 
    bproc.object.sample_poses(objects_to_sample=bop_objs,
                              sample_pose_func=sample_pose_func,
                              max_tries=1000)

    # BVH tree used for camera obstacle checks
    bop_bvh_tree = bproc.object.create_bvh_tree_multi_objects(bop_objs)

    poses = 0
    # Render two camera poses
    while poses < 2:
        # Sample location
        location = bproc.sampler.shell(center=[0, 0, 0],
                                       radius_min=1,
                                       radius_max=1.2,
                                       elevation_min=1,
                                       elevation_max=89,
                                       uniform_volume=False)
        # Determine point of interest in scene as the object closest to the mean of a subset of objects
        poi = bproc.object.compute_poi(bop_objs)
        # Compute rotation based on vector going from location towards poi
        rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location,
                                                                 inplane_rot=np.random.uniform(-0.7854, 0.7854))
        # Add homog cam pose based on location an rotation
        cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)

        # Check that obstacles are at least 0.3 meter away from the camera and make sure the view interesting enough
        if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 0.3}, bop_bvh_tree):
            # Persist camera pose
            bproc.camera.add_camera_pose(cam2world_matrix,
                                         frame=poses)
            poses += 1

    # render the cameras of the current scene
    data = bproc.renderer.render()

    # Write data to bop format
    bproc.writer.write_bop(os.path.join(args.output_dir, 'bop_data'),
                           dataset=args.bop_dataset_name,
                           depths=data["depth"],
                           depth_scale=1.0,
                           colors=data["colors"],
                           color_file_format="JPEG",
                           append_to_existing_output=True)

    # Write data to coco format
    bproc.writer.write_coco_annotations(os.path.join(args.output_dir, 'coco_data'),
                                        supercategory=args.bop_dataset_name,
                                        instance_segmaps=data["instance_segmaps"],
                                        instance_attribute_maps=data["instance_attribute_maps"],
                                        colors=data["colors"],
                                        color_file_format="JPEG",
                                        append_to_existing_output=True)
