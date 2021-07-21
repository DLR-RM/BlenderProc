from src.utility.MaterialUtility import Material
from src.utility.SetupUtility import SetupUtility

SetupUtility.setup([])

from src.utility.Initializer import Initializer
from src.utility.loader.Material import Material
from src.utility.CameraUtility import CameraUtility
from src.utility.LightUtility import Light
from src.utility.RendererUtility import RendererUtility
from src.utility.SegMapRendererUtility import SegMapRendererUtility
from src.utility.CocoWriterUtility import CocoWriterUtility
from src.utility.MathUtility import MathUtility
from src.utility.Utility import Utility
from src.utility.MeshObjectUtility import MeshObject
from src.utility.MaterialUtility import Material
from src.utility.loader.CCMaterialLoader import CCMaterialLoader

import argparse
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('bop_parent_path', nargs='?', help="Path to the bop datasets parent directory")
parser.add_argument('bop_datset_name', nargs='?', help="Main BOP dataset")
parser.add_argument('bop_toolkit_path', nargs='?', help="Path to bop toolkit")
parser.add_argument('cc_textures_path', nargs='?', default="resources/cctextures", help="Path to downloaded cc textures")
parser.add_argument('output_dir', nargs='?', default="examples/bop_object_physics_positioning/output", help="Path to where the final files will be saved ")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
bop_objs = BopLoader.load(
    bop_dataset_path=os.path.join(args.bop_dataset_path, args.bop_dataset_name),
    temp_dir=Utility.get_temporary_directory(),
    sys_paths=args.bop_toolkit_path,
    mm2m=True
)

cc_textures = CCMaterialLoader(args.cc_textures_path)

# Set some category ids for loaded objects
for j, obj in enumerate(bop_objs):
    obj.set_cp("category_id", j)
    obj.enable_rigidbody()
    obj.set_shading_mode('auto')
    
room_planes = [MeshObject.create_primitive('PLANE', scale=[2, 2, 1]),
               MeshObject.create_primitive('PLANE', scale=[2, 2, 1], location=[0, -2, 2], rotation=[-1.570796, 0, 0]),
               MeshObject.create_primitive('PLANE', scale=[2, 2, 1], location=[0, 2, 2], rotation=[1.570796, 0, 0]),
               MeshObject.create_primitive('PLANE', scale=[2, 2, 1], location=[2, 0, 2], rotation=[0, -1.570796, 0]),
               MeshObject.create_primitive('PLANE', scale=[2, 2, 1], location=[-2, 0, 2], rotation=[0, 1.570796, 0])]

for plane in room_planes:
    plane.enable_rigidbody(False, 'BOX')
    plane.add_material()
    
    

light_plane = MeshObject.create_primitive('PLANE', scale=[3, 3, 1], location=[0, 0, 10])
light_plane.set_name('light_plane')
light_plane_material = Material.create()

scenes = np.arange(20)

for scene in scenes:

    emission_color = np.random.uniform([0.5, 0.5, 0.5, 1.0], [1.0, 1.0, 1.0, 1.0])
    emission_strength = np.random.uniform(3,6)
    light_plane_material.make_emissive(emission_strength=emission_strength, 
                                    emission_color=emission_color)



    # define the camera intrinsics
    CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")

    # read the camera positions file and convert into homogeneous camera-world transformation
    with open(args.camera, "r") as f:
        for line in f.readlines():
            line = [float(x) for x in line.split()]
            position, euler_rotation = line[:3], line[3:6]
            matrix_world = MathUtility.build_transformation_mat(position, euler_rotation)
            CameraUtility.add_camera_pose(matrix_world)

    # activate normal and distance rendering
    RendererUtility.enable_normals_output()
    RendererUtility.enable_distance_output()

    # set the amount of samples, which should be used for the color rendering
    RendererUtility.set_samples(50)

    # render the whole pipeline
    data = RendererUtility.render()
    seg_data = SegMapRendererUtility.render(map_by=["instance", "class", "name"])

    # Write data to coco file
    CocoWriterUtility.write(args.output_dir,
                            instance_segmaps=seg_data["instance_segmaps"],
                            instance_attribute_maps=seg_data["instance_attribute_maps"],
                            colors=data["colors"],
                            color_file_format="JPEG")
