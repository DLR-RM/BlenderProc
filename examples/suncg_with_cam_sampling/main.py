from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from src.utility.sampler.SuncgPointInRoomSampler import SuncgPointInRoomSampler
from src.utility.LabelIdMapping import LabelIdMapping
from src.utility.MeshObjectUtility import MeshObject
from src.utility.MaterialLoaderUtility import MaterialLoaderUtility
from src.utility.SegMapRendererUtility import SegMapRendererUtility

from src.utility.Utility import Utility
from src.utility.camera.CameraSampler import CameraSampler
from src.utility.camera.CameraValidation import CameraValidation
from src.utility.loader.SuncgLoader import SuncgLoader


from src.utility.WriterUtility import WriterUtility
from src.utility.Initializer import Initializer

from src.utility.RendererUtility import RendererUtility
import numpy as np
from mathutils import Matrix, Euler

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('output_dir', nargs='?', default="examples/suncg_with_cam_sampling/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
LabelIdMapping.assign_mapping(Utility.resolve_path(os.path.join('resources', 'id_mappings', 'nyu_idset.csv')))
objs = SuncgLoader.load(args.house)

# TODO Migrate to API
Utility.initialize_modules([{"module": "lighting.SuncgLighting"}])[0].run()

point_sampler = SuncgPointInRoomSampler()
bvh_tree = MeshObject.create_bvh_tree_multi_objects([o for o in objs if isinstance(o, MeshObject)])
def sample_pose():
    height = np.random.uniform(0.5, 2)
    location = point_sampler.sample(height)
    rotation = np.random.uniform([1.2217, 0, 0], [1.2217, 0, 6.283185307])
    return Matrix.Translation(location) @ Euler(rotation).to_matrix().to_4x4()

def is_pose_valid(cam2world_matrix, existing_poses):
    if not CameraValidation.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0}, bvh_tree):
        return False
    if CameraValidation.scene_coverage_score(cam2world_matrix) < 0.4:
        return False
    return True

# define the camera intrinsics
CameraSampler.sample(1, sample_pose, is_pose_valid)

# activate normal and distance rendering
RendererUtility.enable_normals_output()
RendererUtility.enable_distance_output()
MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=True)

# render the whole pipeline
data = RendererUtility.render()

data.update(SegMapRendererUtility.render(Utility.get_temporary_directory(), Utility.get_temporary_directory(), "class"))

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
