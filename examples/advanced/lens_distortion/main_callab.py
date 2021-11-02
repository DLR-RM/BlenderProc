import blenderproc as bproc

import argparse

import numpy as np
from mathutils import Matrix

import os # path

parser = argparse.ArgumentParser()
parser.add_argument('scene', help="Path to the scene.obj file, should be examples/resources/scene.obj")
parser.add_argument('config_file', help="Path to the camera calibration config file.")
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

# setup the lens distortion and adapt intrinsics so that it can be later used in the PostProcessing
orig_res_x, orig_res_y, mapping_coords = bproc.camera.set_camera_parameters_from_config_file(args.config_file, read_the_extrinsics=True)

# activate normal and distance rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
bproc.renderer.set_samples(20)

# render the whole pipeline
data = bproc.renderer.render()

# post process the data and apply the lens distortion
for key in ['colors', 'distance', 'normals']:
    # use_interpolation should be false, for semantic segmentation
    data[key] = bproc.postprocessing.apply_lens_distortion(data[key], mapping_coords, orig_res_x, orig_res_y, use_interpolation=True)

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
