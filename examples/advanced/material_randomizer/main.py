import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])


from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.utility.Initializer import Initializer
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.utility.MathUtility import MathUtility

import random
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/material_randomizer/output", help="Path to where the final files, will be saved")
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
bproc.camera.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")

# Add two camera poses
bproc.camera.add_camera_pose(MathUtility.build_transformation_mat([0, -13.741, 4.1242], [1.3, 0, 0]))
bproc.camera.add_camera_pose(MathUtility.build_transformation_mat([1.9488, -6.5202, 0.23291], [1.84, 0, 0.5]))

# Collect all materials
materials = bproc.materials.collect_all()

# Go through all objects
for obj in objs:
    # For each material of the object
    for i in range(len(obj.get_materials())):
        # In 50% of all cases
        if np.random.uniform(0, 1) <= 0.5:
            # Replace the material with a random one
            obj.set_material(i, random.choice(materials))

# set the amount of samples, which should be used for the color rendering
bproc.renderer.set_samples(350)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
