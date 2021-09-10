import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.utility.Initializer import Initializer
from blenderproc.python.writer.BopWriterUtility import BopWriterUtility
from blenderproc.python.postprocessing.PostProcessingUtility import PostProcessingUtility
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.object.OnSurfaceSampler import OnSurfaceSampler
from blenderproc.python.utility.MathUtility import MathUtility
from blenderproc.python.types.MeshObjectUtility import MeshObject

from blenderproc.python.sampler.Shell import Shell
from blenderproc.python.sampler.UpperRegionSampler import UpperRegionSampler

import argparse
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('bop_parent_path', nargs='?', help="Path to the bop datasets parent directory")
parser.add_argument('bop_dataset_name', nargs='?', help="Main BOP dataset")
parser.add_argument('bop_toolkit_path', nargs='?', help="Path to bop toolkit")
parser.add_argument('cc_textures_path', nargs='?', default="resources/cctextures", help="Path to downloaded cc textures")
parser.add_argument('output_dir', nargs='?', default="examples/bop_object_on_surface_sampling/output", help="Path to where the final files will be saved ")
args = parser.parse_args()

Initializer.init()

# load a random sample of bop objects into the scene
sampled_bop_objs = bproc.loader.load_bop(bop_dataset_path = os.path.join(args.bop_parent_path, args.bop_dataset_name),
                                  sys_paths = args.bop_toolkit_path,
                                  mm2m = True,
                                  sample_objects = True,
                                  num_of_objs_to_sample = 10)

# load distractor bop objects
distractor_bop_objs = bproc.loader.load_bop(bop_dataset_path = os.path.join(args.bop_parent_path, 'tless'),
                                     model_type = 'cad',
                                     sys_paths = args.bop_toolkit_path,
                                     mm2m = True,
                                     sample_objects = True,
                                     num_of_objs_to_sample = 3)
distractor_bop_objs += bproc.loader.load_bop(bop_dataset_path = os.path.join(args.bop_parent_path, 'lm'),
                                      sys_paths = args.bop_toolkit_path,
                                      mm2m = True,
                                      sample_objects = True,
                                      num_of_objs_to_sample = 3)

# set shading and physics properties and randomize PBR materials
for j, obj in enumerate(sampled_bop_objs + distractor_bop_objs):
    obj.set_shading_mode('auto')
        
    mat = obj.get_materials()[0]
    if obj.get_cp("bop_dataset_name") in ['itodd', 'tless']:
        grey_col = np.random.uniform(0.3, 0.9)   
        mat.set_principled_shader_value("Base Color", [grey_col, grey_col, grey_col, 1])        
    mat.set_principled_shader_value("Roughness", np.random.uniform(0, 1.0))
    mat.set_principled_shader_value("Specular", np.random.uniform(0, 1.0))
        
# create room
room_planes = [MeshObject.create_primitive('PLANE', scale=[2, 2, 1]),
               MeshObject.create_primitive('PLANE', scale=[2, 2, 1], location=[0, -2, 2], rotation=[-1.570796, 0, 0]),
               MeshObject.create_primitive('PLANE', scale=[2, 2, 1], location=[0, 2, 2], rotation=[1.570796, 0, 0]),
               MeshObject.create_primitive('PLANE', scale=[2, 2, 1], location=[2, 0, 2], rotation=[0, -1.570796, 0]),
               MeshObject.create_primitive('PLANE', scale=[2, 2, 1], location=[-2, 0, 2], rotation=[0, 1.570796, 0])]

# sample light color and strenght from ceiling
light_plane = MeshObject.create_primitive('PLANE', scale=[3, 3, 1], location=[0, 0, 10])
light_plane.set_name('light_plane')
light_plane_material = bproc.Material.create('light_material')
light_plane_material.make_emissive(emission_strength=np.random.uniform(3,6), 
                                   emission_color=np.random.uniform([0.5, 0.5, 0.5, 1.0], [1.0, 1.0, 1.0, 1.0]))    
light_plane.replace_materials(light_plane_material)

# sample point light on shell
light_point = Light()
light_point.set_energy(200)
light_point.set_color(np.random.uniform([0.5, 0.5, 0.5], [1, 1, 1]))
location = Shell.sample(center = [0, 0, 0], radius_min = 1, radius_max = 1.5,
                        elevation_min = 5, elevation_max = 89, uniform_elevation = True)
light_point.set_location(location)

# sample CC Texture and assign to room planes
cc_textures = bproc.loader.load_ccmaterials(args.cc_textures_path)
random_cc_texture = np.random.choice(cc_textures)
for plane in room_planes:
    plane.replace_materials(random_cc_texture)

# Define a function that samples the initial pose of a given object above the ground
def sample_initial_pose(obj: MeshObject):
    obj.set_location(UpperRegionSampler.sample(objects_to_sample_on=room_planes[0:1], 
                                               min_height=1, max_height=4, face_sample_range=[0.4, 0.6]))
    obj.set_rotation_euler(np.random.uniform([0, 0, 0], [0, 0, np.pi * 2]))

# Sample objects on the given surface
placed_objects = OnSurfaceSampler.sample(objects_to_sample=sampled_bop_objs + distractor_bop_objs,
                                         surface=room_planes[0],
                                         sample_pose_func=sample_initial_pose,
                                         min_distance=0.01,
                                         max_distance=0.2)

# BVH tree used for camera obstacle checks
bop_bvh_tree = MeshObject.create_bvh_tree_multi_objects(placed_objects)

poses = 0
while poses < 10:
    # Sample location
    location = Shell.sample(center = [0, 0, 0], 
                            radius_min = 0.61,
                            radius_max = 1.24,
                            elevation_min = 5,
                            elevation_max = 89,
                            uniform_elevation = True)
    # Determine point of interest in scene as the object closest to the mean of a subset of objects
    poi = MeshObject.compute_poi(np.random.choice(placed_objects, size=10))
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
    # Add homog cam pose based on location an rotation
    cam2world_matrix = MathUtility.build_transformation_mat(location, rotation_matrix)
    
    # Check that obstacles are at least 0.3 meter away from the camera and make sure the view interesting enough
    if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 0.3}, bop_bvh_tree):
        # Persist camera pose
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1

# activate distance rendering and set amount of samples for color rendering
bproc.renderer.enable_distance_output()
bproc.renderer.set_samples(50)

# render the whole pipeline
data = bproc.renderer.render()

# Write data in bop format
BopWriterUtility.write(args.output_dir, 
                       dataset = args.bop_dataset_name,
                       depths = PostProcessingUtility.dist2depth(data["distance"]), 
                       colors = data["colors"], 
                       color_file_format = "JPEG",
                       ignore_dist_thres = 10)
