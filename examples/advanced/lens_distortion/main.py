import blenderproc as bproc

import argparse

import numpy as np
import bpy

parser = argparse.ArgumentParser()
parser.add_argument('scene', help="Path to the scene.obj file, should be examples/resources/scene.obj")
#parser.add_argument('config_file', help="Path to the camera calibration config file.")
parser.add_argument('output_dir', help="Path to where the final files, will be saved, could be examples/basics/basic/output")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# set the camera intrinsics by hand
orig_res_x, orig_res_y = 640, 480
cam_K = np.array([[349.554, 0.0, 336.84], [0.0, 349.554, 189.185], [0.0, 0.0, 1.0]])
k1, k2, k3 = -0.172992, 0.0248708, 0.00149384
p1, p2 = 0.000311976, -9.62967e-5
bproc.camera.set_intrinsics_from_K_matrix(cam_K, orig_res_x, orig_res_y, bpy.context.scene.camera.data.clip_start, bpy.context.scene.camera.data.clip_end)
mapping_coords = bproc.camera.set_lens_distortion(k1, k2, k3, p1, p2)
# # Alternatively you can use the calibration file camera_calibration_callab_img0.cal :
# orig_res_x, orig_res_y, mapping_coords = bproc.camera.set_camera_parameters_from_config_file(args.config_file, read_the_extrinsics=False)

# Find point of interest, all cam poses should look towards it
poi = bproc.object.compute_poi(objs)
# Sample five camera poses
for i in range(2):
    # Sample random camera location above objects
    location = np.random.uniform([-10, -10, 12], [10, 10, 8])
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)

# activate normal and distance rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_distance_output(activate_antialiasing=True)

# render the whole pipeline
data = bproc.renderer.render()

# post process the data and apply the lens distortion
for key in ['colors', 'distance', 'normals']:
    # use_interpolation should be false, for everything except colors
    use_interpolation = key == "colors"
    data[key] = bproc.postprocessing.apply_lens_distortion(data[key], mapping_coords, orig_res_x, orig_res_y,
                                                           use_interpolation=use_interpolation)

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
