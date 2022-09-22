import blenderproc as bproc
import random
import os
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('scene_net_obj_path', help="Path to the used scene net `.obj` file, download via scripts/download_scenenet.py")
parser.add_argument('scene_texture_path', help="Path to the downloaded texture files, you can find them at http://tinyurl.com/zpc9ppb")
parser.add_argument('cc_material_path', nargs='?', default="resources/cctextures", help="Path to CCTextures folder, see the /scripts for the download script.")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/scenenet_with_cctextures/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# Load the scenenet room and label its objects with category ids based on the nyu mapping
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
objs = bproc.loader.load_scenenet(args.scene_net_obj_path, args.scene_texture_path, label_mapping)

# Load all recommended cc materials, however don't load their textures yet
cc_materials = bproc.loader.load_ccmaterials(args.cc_material_path, preload=True)

# Go through all objects
for obj in objs:
    # For each material of the object
    for i in range(len(obj.get_materials())):
        # In 40% of all cases
        if np.random.uniform(0, 1) <= 0.4:
            # Replace the material with a random one from cc materials
            obj.set_material(i, random.choice(cc_materials))

# Now load all textures of the materials that were assigned to at least one object
bproc.loader.load_ccmaterials(args.cc_material_path, fill_used_empty_materials=True)

# In some scenes floors, walls and ceilings are one object that needs to be split first
# Collect all walls
walls = bproc.filter.by_cp(objs, "category_id", label_mapping.id_from_label("wall"))
# Extract floors from the objects
new_floors = bproc.object.extract_floor(walls, new_name_for_object="floor", should_skip_if_object_is_already_there=True)
# Set category id of all new floors
for floor in new_floors:
    floor.set_cp("category_id", label_mapping.id_from_label("floor"))
# Add new floors to our total set of objects
objs += new_floors

# Extract ceilings from the objects
new_ceilings = bproc.object.extract_floor(walls, new_name_for_object="ceiling", up_vector_upwards=False, should_skip_if_object_is_already_there=True)
# Set category id of all new ceiling
for ceiling in new_ceilings:
    ceiling.set_cp("category_id", label_mapping.id_from_label("ceiling"))
# Add new ceilings to our total set of objects
objs += new_ceilings

# Make all lamp objects emit light
lamps = bproc.filter.by_attr(objs, "name", ".*[l|L]amp.*", regex=True)
bproc.lighting.light_surface(lamps, emission_strength=15)
# Also let all ceiling objects emit a bit of light, so the whole room gets more bright
ceilings = bproc.filter.by_attr(objs, "name", ".*[c|C]eiling.*", regex=True)
bproc.lighting.light_surface(ceilings, emission_strength=2, emission_color=[1,1,1,1])

# Init bvh tree containing all mesh objects
bvh_tree = bproc.object.create_bvh_tree_multi_objects(objs)

# Find all floors in the scene, so we can sample locations above them
floors = bproc.filter.by_cp(objs, "category_id", label_mapping.id_from_label("floor"))
poses = 0
tries = 0
while tries < 10000 and poses < 5:
    tries += 1
    # Sample point above the floor in height of [1.5m, 1.8m]
    location = bproc.sampler.upper_region(floors, min_height=1.5, max_height=1.8)
    # Check that there is no object between the sampled point and the floor
    _, _, _, _, hit_object, _ = bproc.object.scene_ray_cast(location, [0, 0, -1])
    if hit_object not in floors:
        continue

    # Sample rotation (fix around X and Y axis)
    rotation = np.random.uniform([1.2217, 0, 0], [1.2217, 0, 2 * np.pi])
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation)

    # Check that there is no obstacle in front of the camera closer than 1m
    if not bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0}, bvh_tree):
        continue

    # Check that the interesting score is not too low
    if bproc.camera.scene_coverage_score(cam2world_matrix) < 0.1:
        continue

    # If all checks were passed, add the camera pose
    bproc.camera.add_camera_pose(cam2world_matrix)
    poses += 1

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.enable_segmentation_output(map_by=["category_id"])

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
