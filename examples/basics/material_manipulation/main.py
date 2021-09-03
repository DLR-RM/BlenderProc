import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from pathlib import Path
from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.filter.Filter import Filter
from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.utility.Initializer import Initializer
from blenderproc.python.camera.CameraUtility import CameraUtility
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.utility.MathUtility import MathUtility
from blenderproc.python.renderer.RendererUtility import RendererUtility

import random
import argparse
import bpy


parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/basics/material_manipulation/scene.obj", help="Path to the scene.obj file")
parser.add_argument('image_dir', nargs='?', default="examples/basics/material_manipulation", help="Path to a folder with .jpg textures to be used in the sampling process")
parser.add_argument('output_dir', nargs='?', default="examples/basics/material_manipulation/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")

# Add two camera poses
CameraUtility.add_camera_pose(MathUtility.build_transformation_mat([0, -13.741, 4.1242], [1.3, 0, 0]))
CameraUtility.add_camera_pose(MathUtility.build_transformation_mat([1.9488, -6.5202, 0.23291], [1.84, 0, 0.5]))

# Find all materials
materials = Material.collect_all()

# Find the material of the ground object
ground_material = Filter.one_by_attr(materials, "name", "Material.001")
# Set its displacement based on its base color texture
ground_material.set_displacement_from_principled_shader_value("Base Color", multiply_factor=1.5)

# Collect all jpg images in the specified directory
images = list(Path(args.image_dir).rglob("*.jpg"))
for mat in materials:
    # Load one random image
    image = bpy.data.images.load(filepath=str(random.choice(images)))
    # Set it as base color of the current material
    mat.set_principled_shader_value("Base Color", image)

# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(350)

# render the whole pipeline
data = RendererUtility.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
