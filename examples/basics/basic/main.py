import blenderproc as bproc
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('camera', help="Path to the camera file, should be examples/resources/camera_positions")
parser.add_argument('scene', help="Path to the scene.obj file, should be examples/resources/scene.obj")
parser.add_argument('output_dir', help="Path to where the final files, will be saved, could be examples/basics/basic/output")
args = parser.parse_args()

bproc.init()
sphere = bproc.object.create_primitive("SPHERE")
sphere.set_location([0.5, -0.3, 0.2])
sphere.set_scale([0.1, 0.1, 0.1])
mat = bproc.material.create("sphere")
mat.set_principled_shader_value("Base Color", [1, 0, 0, 1])
sphere.add_material(mat)

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera resolution
K = np.array([[523.1053, 0, 323.9319], [0, 523.1053, 244.0806], [0, 0, 1]])
bproc.camera.set_intrinsics_from_K_matrix(K, 640, 480)
bproc.camera.set_lens_distortion()
# Sample five camera poses
poses = 0
tries = 0
markers = []
world_cam = []
while tries < 10000 and poses < 100:
    poi = np.random.uniform([-3, -3, -3], [3, 3, 3])
    # Sample random camera location above objects
    location = bproc.sampler.part_sphere(center=[0, 0, 0], radius=np.random.uniform(1, 5), mode="SURFACE", dist_above_center=0)
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    marker = bproc.camera.compute_matches(np.array([[[sphere.get_location()]]]), [(np.linalg.inv(cam2world_matrix), cam2world_matrix[:3, 3])], K[None])[0][0][0]
    print(marker)
    
    if 0 <= marker[0] < 640 and 0 <= marker[1] < 480: 
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1
        markers.append(marker)
        world_cam.append(bproc.math.change_source_coordinate_frame_of_transformation_matrix(cam2world_matrix, ["X", "-Y", "-Z"]))

        
# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)

# render the whole pipeline
data = bproc.renderer.render()
data["marker"] = markers
data["frame_world_cam"] = world_cam

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
