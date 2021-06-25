from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from src.utility.Initializer import Initializer
from src.utility.loader.BlendLoader import BlendLoader
from src.utility.CameraUtility import CameraUtility
from src.utility.LightUtility import Light
from src.utility.RendererUtility import RendererUtility
from src.utility.SegMapRendererUtility import SegMapRendererUtility
from src.utility.CocoWriterUtility import CocoWriterUtility
from src.utility.MathUtility import MathUtility

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('camera', help="Path to the camera file, should be examples/coco_annotations/camera_positions")
parser.add_argument('scene', help="Path to the scene.obj file, should be examples/coco_annotations/scene.blend")
parser.add_argument('output_dir', help="Path to where the final files, will be saved, could be examples/coco_annotations/output")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
objs = BlendLoader.load(args.scene)

# Set some category ids for loaded objects
for j,obj in enumerate(objs):
    obj.set_cp("category_id", j)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

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
                        instance_segmaps = seg_data["instance_segmaps"],
                        instance_attribute_maps= seg_data["instance_attribute_maps"],
                        colors = data["colors"], 
                        color_file_format="JPEG")
