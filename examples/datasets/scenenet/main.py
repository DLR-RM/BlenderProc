import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.utility.LabelIdMapping import LabelIdMapping
from blenderproc.python.renderer.SegMapRendererUtility import SegMapRendererUtility
from blenderproc.python.utility.Utility import Utility
from blenderproc.python.filter.Filter import Filter
from blenderproc.python.lighting.SurfaceLighting import SurfaceLighting
from blenderproc.python.object.FloorExtractor import FloorExtractor
from blenderproc.python.sampler.UpperRegionSampler import UpperRegionSampler
from blenderproc.python.utility.MathUtility import MathUtility
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.utility.Initializer import Initializer
from blenderproc.python.renderer.RendererUtility import RendererUtility

import os
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('scene_net_obj_path', help="Path to the used scene net `.obj` file, download via scripts/download_scenenet.py")
parser.add_argument('scene_texture_path', help="Path to the downloaded texture files, you can find them at http://tinyurl.com/zpc9ppb")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/scenenet/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# Load the scenenet room and label its objects with category ids based on the nyu mapping
label_mapping = LabelIdMapping.from_csv(Utility.resolve_path(os.path.join('resources', 'id_mappings', 'nyu_idset.csv')))
objs = bproc.loader.load_scenenet(args.scene_net_obj_path, args.scene_texture_path, label_mapping)

# In some scenes floors, walls and ceilings are one object that needs to be split first
# Collect all walls
walls = Filter.by_cp(objs, "category_id", label_mapping.id_from_label("wall"))
# Extract floors from the objects
new_floors = FloorExtractor.extract(walls, new_name_for_object="floor", should_skip_if_object_is_already_there=True)
# Set category id of all new floors
for floor in new_floors:
    floor.set_cp("category_id", label_mapping.id_from_label("floor"))
# Add new floors to our total set of objects
objs += new_floors

# Extract ceilings from the objects
new_ceilings = FloorExtractor.extract(walls, new_name_for_object="ceiling", up_vector_upwards=False, should_skip_if_object_is_already_there=True)
# Set category id of all new ceiling
for ceiling in new_ceilings:
    ceiling.set_cp("category_id", label_mapping.id_from_label("ceiling"))
# Add new ceilings to our total set of objects
objs += new_ceilings

# Make all lamp objects emit light
lamps = Filter.by_attr(objs, "name", ".*[l|L]amp.*", regex=True)
SurfaceLighting.run(lamps, emission_strength=15, keep_using_base_color=True)
# Also let all ceiling objects emit a bit of light, so the whole room gets more bright
ceilings = Filter.by_attr(objs, "name", ".*[c|C]eiling.*", regex=True)
SurfaceLighting.run(ceilings, emission_strength=2)

# Init bvh tree containing all mesh objects
bvh_tree = MeshObject.create_bvh_tree_multi_objects(objs)

# Find all floors in the scene, so we can sample locations above them
floors = Filter.by_cp(objs, "category_id", label_mapping.id_from_label("floor"))
poses = 0
tries = 0
while tries < 10000 and poses < 5:
    tries += 1
    # Sample point above the floor in height of [1.5m, 1.8m]
    location = UpperRegionSampler.sample(floors, min_height=1.5, max_height=1.8)
    # Check that there is no object between the sampled point and the floor
    _, _, _, _, hit_object, _ = MeshObject.scene_ray_cast(location, [0, 0, -1])
    if hit_object not in floors:
        continue

    # Sample rotation (fix around X and Y axis)
    rotation = np.random.uniform([1.2217, 0, 0], [1.2217, 0, 2 * np.pi])
    cam2world_matrix = MathUtility.build_transformation_mat(location, rotation)

    # Check that there is no obstacle in front of the camera closer than 1m
    if not bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0}, bvh_tree):
        continue

    # Check that the interesting score is not too low
    if bproc.camera.scene_coverage_score(cam2world_matrix) < 0.1:
        continue

    # If all checks were passed, add the camera pose
    bproc.camera.add_camera_pose(cam2world_matrix)
    poses += 1

# activate normal and distance rendering
RendererUtility.enable_normals_output()
RendererUtility.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(350)

# render the whole pipeline
data = RendererUtility.render()
# Also render segmentation images (Use alpha channel from textures)
data.update(SegMapRendererUtility.render(map_by="class", use_alpha_channel=True))

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
