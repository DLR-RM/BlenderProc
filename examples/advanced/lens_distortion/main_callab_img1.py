import blenderproc as bproc

import argparse

import numpy as np
import bpy
from mathutils import Matrix

import os # path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

parser = argparse.ArgumentParser()
parser.add_argument('scene', help="Path to the scene.obj file, should be examples/resources/scene.obj")
parser.add_argument('output_dir', help="Path to where the final files, will be saved, could be examples/basics/basic/output")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
basename = os.path.basename(args.scene)
filename, file_extension = os.path.splitext(basename)
if(file_extension=='.blend'):
    objs = bproc.loader.load_blend(args.scene)
    obj = bproc.filter.one_by_attr(objs, "name", filename)
    obj.set_location([0, 0, 0])
    obj.set_rotation_euler([0, 0, 0])
elif(file_extension=='.obj'):
    objs = bproc.loader.load_obj(args.scene)
    objs[0].set_location([0, 0, 0])
    objs[0].set_rotation_euler([0, 0, 0])
else:
    raise Exception("The extension of the object file is neither .obj nor .blend .")

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([0, 0, -1])
light.set_energy(30)

# set the camera intrinsics
resolution_x, resolution_y = 640, 480
cam_K = np.array([[601.951, 0.00000, 316.271], [0.00000, 601.951, 236.429], [0.0, 0.0, 1.0]])
k1, k2, k3 = 0.131565, -0.270235, 0.
p1, p2 = 0., 0.
bproc.camera.set_intrinsics_from_K_matrix(cam_K, resolution_x, resolution_y,
bpy.context.scene.camera.data.clip_start, bpy.context.scene.camera.data.clip_end)

# apply the lens distortion
# this only adds the necessary mapping to GlobalStorage, so that it can be later used in the PostProcessing
bproc.camera.set_lens_distortion(k1, k2, k3, p1, p2)

# Use a known camera pose (from DLR CalLab)
cam2world = Matrix(([-0.999756082619708, 0.0218268883858996, 0.00338298019529139, 0.0397942297565947],
    [-0.0219506049256179, -0.964809706540961, -0.262030515792922, 0.169496716181271],
    [-0.00245539019255271, -0.262041183334307, 0.965053185999876, -1.07314329461946],
    [0, 0, 0, 1.]))
# OpenCV -> OpenGL
cam2world = bproc.math.change_source_coordinate_frame_of_transformation_matrix(cam2world, ["X", "-Y", "-Z"])
bproc.camera.add_camera_pose(cam2world)

# activate normal and distance rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
bproc.renderer.set_samples(350)

# render the whole pipeline
data = bproc.renderer.render()

# post process the data and apply the lens distortion
for key in data.keys():
    # make sure the input is only an image
    if isinstance(data[key], list) and len(data[key][0].shape) >= 2:
        data[key] = bproc.postprocessing.apply_lens_distortion(data[key])

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
