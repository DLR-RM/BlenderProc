import blenderproc as bproc
import numpy as np
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/suncg_with_improved_mat/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
objs = bproc.loader.load_suncg(args.house, label_mapping)

# makes Suncg objects emit light
bproc.lighting.light_suncg_scene()

# Init sampler for sampling locations inside the loaded suncg house
point_sampler = bproc.sampler.SuncgPointInRoomSampler(objs)
# Init bvh tree containing all mesh objects
bvh_tree = bproc.object.create_bvh_tree_multi_objects([o for o in objs if isinstance(o, bproc.types.MeshObject)])

poses = 0
tries = 0
while tries < 10000 and poses < 5:
    # Sample point inside house
    height = np.random.uniform(1.65, 1.85)
    location, _ = point_sampler.sample(height)
    # Sample rotation (fix around X and Y axis)
    euler_rotation = np.random.uniform([1.2217, 0, 0], [1.2217, 0, 6.283185307])
    cam2world_matrix = bproc.math.build_transformation_mat(location, euler_rotation)

    # Check that obstacles are at least 1 meter away from the camera and make sure the view interesting enough
    if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0}, bvh_tree) and bproc.camera.scene_coverage_score(cam2world_matrix) > 0.4:
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# improve the materials, first use all materials and only filter the relevant materials out
all_materials = bproc.material.collect_all()
all_wood_materials = bproc.filter.by_attr(all_materials, "name", "wood.*|laminate.*|beam.*", regex=True)

# now change the used values
for material in all_wood_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.05, 0.5))
    material.set_principled_shader_value("Specular", np.random.uniform(0.5, 1.0))
    material.set_displacement_from_principled_shader_value("Base Color", np.random.uniform(0.001, 0.15))

all_stone_materials = bproc.filter.by_attr(all_materials, "name", "tile.*|brick.*|stone.*", regex=True)

# now change the used values
for material in all_stone_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.0, 0.2))
    material.set_principled_shader_value("Specular", np.random.uniform(0.9, 1.0))

all_floor_materials = bproc.filter.by_attr(all_materials, "name", "carpet.*|textile.*", regex=True)

# now change the used values
for material in all_floor_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.5, 1.0))
    material.set_principled_shader_value("Specular", np.random.uniform(0.1, 0.3))

# set the light bounces
bproc.renderer.set_light_bounces(diffuse_bounces=200, glossy_bounces=200, max_bounces=200, transmission_bounces=200, transparent_max_bounces=200)

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.enable_segmentation_output(map_by=["category_id"])

bproc.material.add_alpha_channel_to_textures(blurry_edges=True)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
