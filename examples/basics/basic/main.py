import blenderproc as bproc
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('camera', help="Path to the camera file, should be examples/resources/camera_positions")
parser.add_argument('scene', help="Path to the scene.obj file, should be examples/resources/scene.obj")
parser.add_argument('output_dir', help="Path to where the final files, will be saved, could be examples/basics/basic/output")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
#objs = bproc.loader.load_obj(args.scene)
objs = bproc.loader.load_blend("/home/domin/Downloads/intro.blend")

for obj in objs:
    if obj.get_name() == "Sphere":
        obj.set_cp("category_id", 2)
    else:
        obj.set_cp("category_id", 1)

import bpy
import numpy as np
bpy.context.scene.frame_start = 122
bpy.context.scene.frame_end = 122

matrix_world = bproc.math.build_transformation_mat([0,-2.707,0], [np.pi / 2, 0, 0])
bproc.camera.add_camera_pose(matrix_world)

# define the camera resolution
bproc.camera.set_resolution(3500, 1080)

# activate normal and distance rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output()
bproc.renderer.enable_distance_output()
# set the amount of samples, which should be used for the color rendering
bproc.renderer.set_samples(10)
bproc.renderer.set_output_format(enable_transparency=True)
# render the whole pipeline
data = bproc.renderer.render()
data.update(bproc.renderer.render_segmap(map_by=["instance", "name"]))
data.update(bproc.renderer.render_nocs())
print(data.keys())
# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
