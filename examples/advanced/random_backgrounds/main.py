from blenderproc.python.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.CocoWriterUtility import CocoWriterUtility
from blenderproc.python.SegMapRendererUtility import SegMapRendererUtility
from blenderproc.python.camera.CameraValidation import CameraValidation
from blenderproc.python.sampler.Shell import Shell
from blenderproc.python.MathUtility import MathUtility
from blenderproc.python.CameraUtility import CameraUtility
from blenderproc.python.Initializer import Initializer
from blenderproc.python.loader.ObjectLoader import ObjectLoader
from blenderproc.python.LightUtility import Light
from blenderproc.python.RendererUtility import RendererUtility

import numpy as np
import argparse
import random

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/advanced/random_backgrounds/object.ply", help="Path to the object file.")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/random_backgrounds/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
obj = ObjectLoader.load(args.scene)[0]

# Randomly perturbate the material of the object
mat = obj.get_materials()[0]
mat.set_principled_shader_value("Specular", random.uniform(0, 1))
mat.set_principled_shader_value("Roughness", random.uniform(0, 1))
mat.set_principled_shader_value("Base Color", np.random.uniform([0, 0, 0, 1], [1, 1, 1, 1]))
mat.set_principled_shader_value("Metallic", random.uniform(0, 1))

# Create a new light
light = Light()
light.set_type("POINT")
# Sample its location around the object
light.set_location(Shell.sample(
    center=obj.get_location(),
    radius_min=1,
    radius_max=5,
    elevation_min=1,
    elevation_max=89,
    uniform_elevation=True
))
# Randomly set the color and energy
light.set_color(np.random.uniform([0.5, 0.5, 0.5], [1, 1, 1]))
light.set_energy(random.uniform(100, 1000))

CameraUtility.set_intrinsics_from_blender_params(1, 640, 480, lens_unit="FOV")

# Sample five camera poses
poses = 0
tries = 0
while tries < 10000 and poses < 5:
    # Sample random camera location around the object
    location = Shell.sample(
        center=obj.get_location(),
        radius_min=1,
        radius_max=4,
        elevation_min=1,
        elevation_max=89,
        uniform_elevation=True
    )
    # Compute rotation based lookat point which is placed randomly around the object
    lookat_point = obj.get_location() + np.random.uniform([-0.5, -0.5, -0.5], [0.5, 0.5, 0.5])
    rotation_matrix = CameraUtility.rotation_from_forward_vec(lookat_point - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
    # Add homog cam pose based on location an rotation
    cam2world_matrix = MathUtility.build_transformation_mat(location, rotation_matrix)

    # Only add camera pose if object is still visible
    if obj in CameraValidation.visible_objects(cam2world_matrix):
        CameraUtility.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# Enable transparency so the background becomes transparent
RendererUtility.set_output_format("PNG", enable_transparency=True)

# Render RGB images
data = RendererUtility.render()

# Render segmentation images
seg_data = SegMapRendererUtility.render(map_by=["instance", "class", "name"], default_values={"class": 0, "name": "none"})

# Write data to coco file
CocoWriterUtility.write(args.output_dir,
                        instance_segmaps=seg_data["instance_segmaps"],
                        instance_attribute_maps=seg_data["instance_attribute_maps"],
                        colors=data["colors"],
                        append_to_existing_output=True)
