import blenderproc as bproc
import argparse
import numpy as np
import random
import os

parser = argparse.ArgumentParser()
parser.add_argument('shapenet_path', help="Path to the downloaded shape net core v2 dataset, get it [here](http://www.shapenet.org/)")
parser.add_argument('vhacd_path', nargs='?', default="blenderproc_resources/vhacd", help="The directory in which vhacd should be installed or is already installed.")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/multi_render/output", help="Path to where the final files, will be saved")
parser.add_argument('--runs', default=10, type=int, help="The number of times the objects should be repositioned and rendered using 2 to 5 random camera poses.")
args = parser.parse_args()

bproc.init()

# Load multiple objects from ShapeNet
shapenet_objs = []
for synset_id, source_id in [("02801938", "d9fb327b0e19a9ddc735651f0fb19093"), ("02880940", "a9ba34614bfd8ca9938afc5c0b5b182"), ("02691156", "56c605d0b1bd86a9f417244ad1b14759"), ("04380533", "102273fdf8d1b90041fbc1e2da054acb"), ("02954340", "1fd62459ef715e71617fb5e58b4b0232")]:
    shapenet_objs.append(bproc.loader.load_shapenet(args.shapenet_path, synset_id, source_id))

# Go over all ShapeNet objects
for shapenet_obj in shapenet_objs:
    # Make the object actively participate in the physics simulation
    shapenet_obj.enable_rigidbody(active=True, collision_shape="COMPOUND")
    # Also use convex decomposition as collision shapes
    shapenet_obj.build_convex_decomposition_collision_shape(args.vhacd_path)

# Create a ground plane
plane = bproc.object.create_primitive('PLANE', scale=[20, 20, 1])
plane.enable_rigidbody(False, collision_shape='BOX')

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
bproc.camera.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")
bproc.renderer.enable_segmentation_output(map_by=["instance", "name"])

# Do multiple times: Position the shapenet objects using the physics simulator and render between 2 and 5 images with random camera poses
for r in range(args.runs):
    # Clear all key frames from the previous run
    bproc.utility.reset_keyframes()

    # Define a function that samples 6-DoF poses
    def sample_pose(obj: bproc.types.MeshObject):
        obj.set_location(np.random.uniform([-1, -1, 0], [1, 1, 2]))
        obj.set_rotation_euler(bproc.sampler.uniformSO3())

    # Sample the poses of all shapenet objects above the ground without any collisions in-between
    bproc.object.sample_poses(
        shapenet_objs,
        objects_to_check_collisions=shapenet_objs + [plane],
        sample_pose_func=sample_pose
    )

    # Run the simulation and fix the poses of the shapenet objects at the end
    bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=4, max_simulation_time=20, check_object_interval=1)

    # Find point of interest, all cam poses should look towards it
    poi = bproc.object.compute_poi(shapenet_objs)
    # Sample up to five camera poses
    for i in range(random.randint(2, 5)):
        # Sample location
        location = bproc.sampler.shell(center=[0, 0, 0],
                                       radius_min=3,
                                       radius_max=5,
                                       elevation_min=5,
                                       elevation_max=89)
        # Compute rotation based on vector going from location towards poi
        rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
        # Add homog cam pose based on location an rotation
        cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
        bproc.camera.add_camera_pose(cam2world_matrix)

    # render the whole pipeline
    data = bproc.renderer.render()

    # write the data to a .hdf5 container in the run-specific output directory
    bproc.writer.write_hdf5(os.path.join(args.output_dir, str(r)), data)
