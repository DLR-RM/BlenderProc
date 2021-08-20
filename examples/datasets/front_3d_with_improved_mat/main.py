from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

import argparse
import os
import numpy as np
import random

from src.utility.filter.Filter import Filter
from src.utility.loader.CCMaterialLoader import CCMaterialLoader
from src.utility.Initializer import Initializer
from src.utility.LabelIdMapping import LabelIdMapping
from src.utility.loader.Front3DLoader import Front3DLoader
from src.utility.sampler.Front3DPointInRoomSampler import Front3DPointInRoomSampler
from src.utility.MeshObjectUtility import MeshObject
from src.utility.MathUtility import MathUtility
from src.utility.camera.CameraValidation import CameraValidation
from src.utility.CameraUtility import CameraUtility
from src.utility.WriterUtility import WriterUtility
from src.utility.Utility import Utility
from src.utility.RendererUtility import RendererUtility
from src.utility.SegMapRendererUtility import SegMapRendererUtility

parser = argparse.ArgumentParser()
parser.add_argument("front", help="Path to the 3D front file")
parser.add_argument("future_folder", help="Path to the 3D Future Model folder.")
parser.add_argument("front_3D_texture_path", help="Path to the 3D FRONT texture folder.")
parser.add_argument('cc_material_path', nargs='?', default="resources/cctextures", help="Path to CCTextures folder, see the /scripts for the download script.")
parser.add_argument("output_dir", nargs='?', default="examples/datasets/front_3d_with_improved_mat/output", help="Path to where the data should be saved")
args = parser.parse_args()

if not os.path.exists(args.front) or not os.path.exists(args.future_folder):
    raise Exception("One of the two folders does not exist!")

Initializer.init()
mapping_file = Utility.resolve_path(os.path.join("resources", "front_3D", "3D_front_mapping.csv"))
mapping = LabelIdMapping.from_csv(mapping_file)

# set the light bounces
RendererUtility.set_light_bounces(diffuse_bounces=200, glossy_bounces=200, max_bounces=200,
                                  transmission_bounces=200, transparent_max_bounces=200)

# load the front 3D objects
loaded_objects = Front3DLoader.load(
    json_path=args.front,
    future_model_path=args.future_folder,
    front_3D_texture_path=args.front_3D_texture_path,
    label_mapping=mapping
)

cc_materials = CCMaterialLoader.load(args.cc_material_path, ["Bricks", "Wood", "Carpet", "Tile", "Marble"])

floors = Filter.by_attr(loaded_objects, "name", "Floor.*", regex=True)
for floor in floors:
    # For each material of the object
    for i in range(len(floor.get_materials())):
        # In 95% of all cases
        if np.random.uniform(0, 1) <= 0.95:
            # Replace the material with a random one
            floor.set_material(i, random.choice(cc_materials))


baseboards_and_doors = Filter.by_attr(loaded_objects, "name", "Baseboard.*|Door.*", regex=True)
wood_floor_materials = Filter.by_cp(cc_materials, "asset_name", "WoodFloor.*", regex=True)
for obj in baseboards_and_doors:
    # For each material of the object
    for i in range(len(obj.get_materials())):
        # Replace the material with a random one
        obj.set_material(i, random.choice(wood_floor_materials))


walls = Filter.by_attr(loaded_objects, "name", "Wall.*", regex=True)
marble_materials = Filter.by_cp(cc_materials, "asset_name", "Marble.*", regex=True)
for wall in walls:
    # For each material of the object
    for i in range(len(wall.get_materials())):
        # In 50% of all cases
        if np.random.uniform(0, 1) <= 0.1:
            # Replace the material with a random one
            wall.set_material(i, random.choice(marble_materials))

# Init sampler for sampling locations inside the loaded front3D house
point_sampler = Front3DPointInRoomSampler(loaded_objects)

# Init bvh tree containing all mesh objects
bvh_tree = MeshObject.create_bvh_tree_multi_objects([o for o in loaded_objects if isinstance(o, MeshObject)])

poses = 0
tries = 0

def check_name(name):
    for category_name in ["chair", "sofa", "table", "bed"]:
        if category_name in name.lower():
            return True
    return False

# filter some objects from the loaded objects, which are later used in calculating an interesting score
special_objects = [obj.get_cp("category_id") for obj in loaded_objects if check_name(obj.get_name())]

proximity_checks = {"min": 1.0, "avg": {"min": 2.5, "max": 3.5}, "no_background": True}
while tries < 10000 and poses < 10:
    # Sample point inside house
    height = np.random.uniform(1.4, 1.8)
    location = point_sampler.sample(height)
    # Sample rotation (fix around X and Y axis)
    rotation = np.random.uniform([1.2217, 0, 0], [1.338, 0, np.pi * 2])
    cam2world_matrix = MathUtility.build_transformation_mat(location, rotation)

    # Check that obstacles are at least 1 meter away from the camera and have an average distance between 2.5 and 3.5
    # meters and make sure that no background is visible, finally make sure the view is interesting enough
    if CameraValidation.scene_coverage_score(cam2world_matrix, special_objects, special_objects_weight=10.0) > 0.8 \
            and CameraValidation.perform_obstacle_in_view_check(cam2world_matrix, proximity_checks, bvh_tree):
        CameraUtility.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# Also render normals
RendererUtility.enable_normals_output()
# set the sample amount to 350
RendererUtility.set_samples(350)

# render the whole pipeline
data = RendererUtility.render()
data.update(SegMapRendererUtility.render(map_by="class"))

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
