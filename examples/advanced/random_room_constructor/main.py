from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from src.utility.CameraUtility import CameraUtility
from src.utility.MathUtility import MathUtility
from src.utility.MeshObjectUtility import MeshObject
from src.utility.camera.CameraValidation import CameraValidation
from src.utility.sampler.UpperRegionSampler import UpperRegionSampler
from src.utility.constructor.RandomRoomConstructor import RandomRoomConstructor
from src.utility.lighting.SurfaceLighting import SurfaceLighting
from src.utility.loader.CCMaterialLoader import CCMaterialLoader
from src.utility.loader.IKEALoader import IKEALoader
from src.utility.WriterUtility import WriterUtility
from src.utility.Initializer import Initializer

from src.utility.RendererUtility import RendererUtility
from src.utility.PostProcessingUtility import PostProcessingUtility

import argparse
import numpy as np
from mathutils import Euler


parser = argparse.ArgumentParser()
parser.add_argument('ikea_path', nargs='?', default="resources/ikea", help="Path to the downloaded IKEA dataset, see the /scripts for the download script")
parser.add_argument('cc_material_path', nargs='?', default="resources/cctextures", help="Path to CCTextures folder, see the /scripts for the download script.")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/random_room_constructor/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# Load materials and objects that can be placed into the room
materials = CCMaterialLoader.load(args.cc_material_path, ["Bricks", "Wood", "Carpet", "Tile", "Marble"])
interior_objects = []
for i in range(15):
    interior_objects.extend(IKEALoader.load(args.ikea_path, ["bed", "chair", "desk", "bookshelf"]))

# Construct random room and fill with interior_objects
objects = RandomRoomConstructor.construct(25, interior_objects, materials, amount_of_extrusions=5)

# Bring light into the room
SurfaceLighting.run([obj for obj in objects if obj.get_name() == "Ceiling"], emission_strength=4.0)

# Init bvh tree containing all mesh objects
bvh_tree = MeshObject.create_bvh_tree_multi_objects(objects)
floor = [obj for obj in objects if obj.get_name() == "Floor"][0]
poses = 0
tries = 0
while tries < 10000 and poses < 5:
    # Sample point
    location = UpperRegionSampler.sample(floor, min_height=1.5, max_height=1.8)
    # Sample rotation
    rotation = np.random.uniform([1.0, 0, 0], [1.4217, 0, 6.283185307])
    cam2world_matrix = MathUtility.build_transformation_mat(location, rotation)

    # Check that obstacles are at least 1 meter away from the camera and make sure the view interesting enough
    if CameraValidation.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.2}, bvh_tree) and \
            CameraValidation.scene_coverage_score(cam2world_matrix) > 0.4 and \
            floor.position_is_above_object(location):
        # Persist camera pose
        CameraUtility.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# activate distance rendering
RendererUtility.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(350)
RendererUtility.set_light_bounces(max_bounces=200, diffuse_bounces=200, glossy_bounces=200, transmission_bounces=200, transparent_max_bounces=200)
# render the whole pipeline
data = RendererUtility.render()

# post process the data and remove the redundant channels in the distance image
data["depth"] = PostProcessingUtility.dist2depth(data["distance"])
del data["distance"]

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
