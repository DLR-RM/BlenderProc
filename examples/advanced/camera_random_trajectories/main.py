import blenderproc as bproc
import numpy as np
import argparse
import mathutils

from blenderproc.python.utility.SetupUtility import SetupUtility

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/camera_random_trajectories/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Find point of interest, all cam poses should look towards it
poi = bproc.object.compute_poi(objs)

# Add translational random walk on top of the POI
poi_drift = bproc.sampler.random_walk(total_length = 25, dims = 3, step_magnitude = 0.005, 
                                      window_size = 5, interval = [-0.03, 0.03], distribution = 'uniform')

# Rotational camera shaking as a random walk: Sample an axis angle representation
camera_shaking_rot_angle = bproc.sampler.random_walk(total_length = 25, dims = 1, step_magnitude = np.pi/32, window_size = 5,
                                                     interval = [-np.pi/6, np.pi/6], distribution = 'uniform', order = 2)
camera_shaking_rot_axis = bproc.sampler.random_walk(total_length = 25, dims = 3, window_size = 10, distribution = 'normal')
camera_shaking_rot_axis /= np.linalg.norm(camera_shaking_rot_axis, axis=1, keepdims=True)

for i in range(25):
    # Camera trajectory that defines a quater circle at constant height 
    location_cam = np.array([10*np.cos(i/25 * np.pi), 10*np.sin(i/25 * np.pi), 8])
    # Compute rotation based on vector going from location towards poi + drift
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi + poi_drift[i] - location_cam)
    # random walk axis-angle -> rotation matrix
    R_rand = np.array(mathutils.Matrix.Rotation(camera_shaking_rot_angle[i], 3, camera_shaking_rot_axis[i]))
    # Add the random walk to the camera rotation 
    rotation_matrix = R_rand @ rotation_matrix
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location_cam, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)

# Set max samples for quick rendering
bproc.renderer.set_max_amount_of_samples(50)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)

# write the animations into .gif files
bproc.writer.write_gif_animation(args.output_dir, data, frame_duration_in_ms=80)