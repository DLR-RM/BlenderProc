import blenderproc as bproc
"""
The quickstart example:

1. A monkey object is created plus a light, which illuminates the monkey.
2. A light is created, placed and gets a proper energy level set
3. The camera is placed in the scene to look at the monkey
4. A color image is rendered
5. The rendered image is saved in an .hdf5 file container

"""

import numpy as np

bproc.init()

# Create a simple object:
obj = bproc.object.create_primitive("MONKEY")

# Create a point light next to it
light = bproc.types.Light()
light.set_location([2, -2, 0])
light.set_energy(300)

# Set the camera to be in front of the object
cam_pose = bproc.math.build_transformation_mat([0, -5, 0], [np.pi / 2, 0, 0])
bproc.camera.add_camera_pose(cam_pose)

# Render the scene
data = bproc.renderer.render()

# Write the rendering into a hdf5 file
bproc.writer.write_hdf5("output/", data)
