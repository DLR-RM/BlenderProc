import blenderproc as bproc
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('shape_net', help="path to the downloaded shape net core v2 dataset, get it from (http://www.shapenet.org/)")
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/shapenet_with_suncg/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load suncg house into the scene
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
suncg_objs = bproc.loader.load_suncg(args.house, label_mapping=label_mapping)

# Find all bed objects, to sample the shapenet objects on
bed_objs = bproc.filter.by_cp(suncg_objs, "category_id", label_mapping.id_from_label("bed"))

# makes Suncg objects emit light
bproc.lighting.light_suncg_scene()

# load selected shapenet object
shapenet_obj = bproc.loader.load_shapenet(args.shape_net, used_synset_id="02801938")

# Sample a point above any bed
sample_point = bproc.sampler.upper_region(
    objects_to_sample_on=bed_objs,
    min_height=0.75,
    use_ray_trace_check=True
)
# move the shapenet object to the sampled position
shapenet_obj.set_location(sample_point)

# adding a modifier we avoid that the objects falls through other objects during the physics simulation
shapenet_obj.add_modifier(name="SOLIDIFY", thickness=0.001)

# enable rigid body component of the objects which makes them participate in physics simulations
shapenet_obj.enable_rigidbody(active=True, mass_factor=2000, collision_margin=0.0001)
for obj in bproc.filter.all_with_type(suncg_objs, bproc.types.MeshObject):
    obj.enable_rigidbody(active=False, mass_factor=2000, collision_margin=0.0001)

# Run the physics simulation
bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=0.5, max_simulation_time=4, check_object_interval=0.25)

# sample five camera poses
for i in range(5):
    # sample random camera location around the shapenet object
    location = bproc.sampler.part_sphere(center=shapenet_obj.get_location(), mode="SURFACE", radius=2, dist_above_center=0.5)
    # compute rotation based on vector going from the camera location towards shapenet object
    rotation_matrix = bproc.camera.rotation_from_forward_vec(shapenet_obj.get_location() - location)
    # add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
