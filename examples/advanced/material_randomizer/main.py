import blenderproc as bproc
import random
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/material_randomizer/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
bproc.camera.set_resolution(512, 512)

# Add two camera poses
bproc.camera.add_camera_pose(bproc.math.build_transformation_mat([0, -13.741, 4.1242], [1.3, 0, 0]))
bproc.camera.add_camera_pose(bproc.math.build_transformation_mat([1.9488, -6.5202, 0.23291], [1.84, 0, 0.5]))

# Collect all materials
materials = bproc.material.collect_all()

# Go through all objects
for obj in objs:
    # For each material of the object
    for i in range(len(obj.get_materials())):
        # In 50% of all cases
        if np.random.uniform(0, 1) <= 0.5:
            # Replace the material with a random one
            obj.set_material(i, random.choice(materials))

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
