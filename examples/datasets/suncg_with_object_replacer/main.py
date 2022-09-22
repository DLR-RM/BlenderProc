import blenderproc as bproc
import numpy as np
from mathutils import Euler
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('object_path', help='Path to the chair object which will be used to replace others.')
parser.add_argument('output_dir', nargs='?', default="examples/datasets/suncg_with_object_replacer/output",
                    help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
objs = bproc.loader.load_suncg(args.house, label_mapping)

# replace some objects with others

chair_obj = bproc.loader.load_obj(args.object_path)
if len(chair_obj) != 1:
    raise Exception(f"There should only be one chair object not: {len(chair_obj)}")
chair_obj = chair_obj[0]


def relative_pose_sampler(obj):
    # Sample random rotation and apply it to the objects pose
    obj.blender_obj.rotation_euler.rotate(Euler((0, 0, np.random.uniform(0.0, 6.283185307))))


replace_ratio = 1.0
bproc.object.replace_objects(
    objects_to_be_replaced=bproc.filter.by_cp(objs, "coarse_grained_class", "chair"),
    objects_to_replace_with=[chair_obj],
    ignore_collision_with=bproc.filter.by_cp(objs, "suncg_type", "Floor"),
    replace_ratio=replace_ratio,
    copy_properties=True,
    relative_pose_sampler=relative_pose_sampler
)

# some objects won't be valid anymore
objs = [obj for obj in objs if obj.is_valid()]

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
    height = np.random.uniform(0.5, 2)
    location, _ = point_sampler.sample(height)
    # Sample rotation (fix around X and Y axis)
    euler_rotation = np.random.uniform([1.2217, 0, 0], [1.2217, 0, 6.283185307])
    cam2world_matrix = bproc.math.build_transformation_mat(location, euler_rotation)

    # Check that obstacles are at least 1 meter away from the camera and make sure the view interesting enough
    if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0},
                                                       bvh_tree) and bproc.camera.scene_coverage_score(
            cam2world_matrix) > 0.4:
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.material.add_alpha_channel_to_textures(blurry_edges=True)
bproc.renderer.enable_segmentation_output(map_by=["category_id"])

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
