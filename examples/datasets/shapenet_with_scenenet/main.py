import blenderproc as bproc
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('scene_net_obj_path', help="Path to the used scene net `.obj` file, download via 'blenderproc download scenenet'")
parser.add_argument('scene_texture_path', help="Path to the downloaded texture files, you can find them at http://tinyurl.com/zpc9ppb")
parser.add_argument('shapenet_path', help="Path to the downloaded shape net core v2 dataset, get it from http://www.shapenet.org/")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/shapenet_with_scenenet/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# Load the scenenet room and label its objects with category ids based on the nyu mapping
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
room_objs = bproc.loader.load_scenenet(args.scene_net_obj_path, args.scene_texture_path, label_mapping)

# In some scenes floors, walls and ceilings are one object that needs to be split first
# Collect all walls
walls = bproc.filter.by_cp(room_objs, "category_id", label_mapping.id_from_label("wall"))
# Extract floors from the objects
new_floors = bproc.object.extract_floor(walls, new_name_for_object="floor", should_skip_if_object_is_already_there=True)
# Set category id of all new floors
for floor in new_floors:
    floor.set_cp("category_id", label_mapping.id_from_label("floor"))
# Add new floors to our total set of objects
room_objs += new_floors

# Extract ceilings from the objects
new_ceilings = bproc.object.extract_floor(walls, new_name_for_object="ceiling", up_vector_upwards=False, should_skip_if_object_is_already_there=True)
# Set category id of all new ceiling
for ceiling in new_ceilings:
    ceiling.set_cp("category_id", label_mapping.id_from_label("ceiling"))
# Add new ceilings to our total set of objects
room_objs += new_ceilings

# Make all lamp objects emit light
lamps = bproc.filter.by_attr(room_objs, "name", ".*[l|L]amp.*", regex=True)
bproc.lighting.light_surface(lamps, emission_strength=15)
# Also let all ceiling objects emit a bit of light, so the whole room gets more bright
ceilings = bproc.filter.by_attr(room_objs, "name", ".*[c|C]eiling.*", regex=True)
bproc.lighting.light_surface(ceilings, emission_strength=2, emission_color=[1,1,1,1])

# load the ShapeNet object into the scene
shapenet_obj = bproc.loader.load_shapenet(args.shapenet_path, used_synset_id="02801938")

# Collect all beds
beds = bproc.filter.by_cp(room_objs, "category_id", label_mapping.id_from_label("bed"))
# Sample the location of the ShapeNet object above a random bed
shapenet_obj.set_location(bproc.sampler.upper_region(beds, min_height=0.3, use_ray_trace_check=True))

# Make sure the ShapeNet object has a minimum thickness (this will increase the stability of the simulator)
shapenet_obj.add_modifier("SOLIDIFY", thickness=0.0025)
# Make the ShapeNet object actively participating in the simulation and increase its mass to stabilize the simulation
shapenet_obj.enable_rigidbody(True, mass_factor=2000, collision_margin=0.00001, collision_shape="MESH")
# Make all other objects passively participating in the simulation as obstacles and increase its mass to stabilize the simulation
for obj in room_objs:
    obj.enable_rigidbody(False, mass_factor=2000, collision_margin=0.00001, collision_shape="MESH")

# Run the simulation to let the ShapeNet object fall onto the bed
bproc.object.simulate_physics_and_fix_final_poses(
    solver_iters=30,
    substeps_per_frame=40,
    min_simulation_time=0.5,
    max_simulation_time=4,
    check_object_interval=0.25
)

# Init bvh tree containing all mesh objects
bvh_tree = bproc.object.create_bvh_tree_multi_objects(room_objs)
poses = 0
tries = 0
while tries < 10000 and poses < 5:
    # Sample on sphere around ShapeNet object
    location = bproc.sampler.part_sphere(shapenet_obj.get_location(), radius=2, dist_above_center=0.5, mode="SURFACE")
    # Compute rotation based on vector going from location towards ShapeNet object
    rotation_matrix = bproc.camera.rotation_from_forward_vec(shapenet_obj.get_location() - location)
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)

    # Check that obstacles are at least 0.5 meter away from the camera and that the ShapeNet object is visible
    if shapenet_obj in bproc.camera.visible_objects(cam2world_matrix) and bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 0.5}, bvh_tree):
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
