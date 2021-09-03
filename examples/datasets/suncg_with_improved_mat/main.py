from blenderproc.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.utility.CameraUtility import CameraUtility
from blenderproc.utility.MathUtility import MathUtility
from blenderproc.utility.MaterialUtility import Material
from blenderproc.utility.filter.Filter import Filter
from blenderproc.utility.sampler.SuncgPointInRoomSampler import SuncgPointInRoomSampler
from blenderproc.utility.LabelIdMapping import LabelIdMapping
from blenderproc.utility.MeshObjectUtility import MeshObject
from blenderproc.utility.MaterialLoaderUtility import MaterialLoaderUtility
from blenderproc.utility.SegMapRendererUtility import SegMapRendererUtility

from blenderproc.utility.Utility import Utility
from blenderproc.utility.camera.CameraValidation import CameraValidation
from blenderproc.utility.loader.SuncgLoader import SuncgLoader
from blenderproc.utility.lighting.SuncgLighting import SuncgLighting

from blenderproc.utility.WriterUtility import WriterUtility
from blenderproc.utility.Initializer import Initializer

from blenderproc.utility.RendererUtility import RendererUtility
import numpy as np

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/suncg_with_improved_mat/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
label_mapping = LabelIdMapping.from_csv(Utility.resolve_path(os.path.join('resources', 'id_mappings', 'nyu_idset.csv')))
objs = SuncgLoader.load(args.house, label_mapping)

# makes Suncg objects emit light
SuncgLighting.light()

# Init sampler for sampling locations inside the loaded suncg house
point_sampler = SuncgPointInRoomSampler(objs)
# Init bvh tree containing all mesh objects
bvh_tree = MeshObject.create_bvh_tree_multi_objects([o for o in objs if isinstance(o, MeshObject)])

poses = 0
tries = 0
while tries < 10000 and poses < 5:
    # Sample point inside house
    height = np.random.uniform(1.65, 1.85)
    location, _ = point_sampler.sample(height)
    # Sample rotation (fix around X and Y axis)
    euler_rotation = np.random.uniform([1.2217, 0, 0], [1.2217, 0, 6.283185307])
    cam2world_matrix = MathUtility.build_transformation_mat(location, euler_rotation)

    # Check that obstacles are at least 1 meter away from the camera and make sure the view interesting enough
    if CameraValidation.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0}, bvh_tree) and CameraValidation.scene_coverage_score(cam2world_matrix) > 0.4:
        CameraUtility.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# improve the materials, first use all materials and only filter the relevant materials out
all_materials = Material.collect_all()
all_wood_materials = Filter.by_attr(all_materials, "name", "wood.*|laminate.*|beam.*", regex=True)

# now change the used values
for material in all_wood_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.05, 0.5))
    material.set_principled_shader_value("Specular", np.random.uniform(0.5, 1.0))
    material.set_displacement_from_principled_shader_value("Base Color", np.random.uniform(0.001, 0.15))

all_stone_materials = Filter.by_attr(all_materials, "name", "tile.*|brick.*|stone.*", regex=True)

# now change the used values
for material in all_stone_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.0, 0.2))
    material.set_principled_shader_value("Specular", np.random.uniform(0.9, 1.0))

all_floor_materials = Filter.by_attr(all_materials, "name", "carpet.*|textile.*", regex=True)

# now change the used values
for material in all_floor_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.5, 1.0))
    material.set_principled_shader_value("Specular", np.random.uniform(0.1, 0.3))

# set the light bounces
RendererUtility.set_light_bounces(diffuse_bounces=200, glossy_bounces=200, max_bounces=200, transmission_bounces=200, transparent_max_bounces=200)

# activate normal and distance rendering
RendererUtility.enable_normals_output()
RendererUtility.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(350)

MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=True)

# render the whole pipeline
data = RendererUtility.render()

data.update(SegMapRendererUtility.render(map_by="class", use_alpha_channel=True))

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
