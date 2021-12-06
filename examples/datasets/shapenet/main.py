import blenderproc as bproc
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('shapenet_path', help="Path to the downloaded shape net core v2 dataset, get it from http://www.shapenet.org/")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/shapenet/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the ShapeNet object into the scene
shapenet_obj = bproc.loader.load_shapenet(args.shapenet_path, used_synset_id="02691156", used_source_id="10155655850468db78d106ce0a280f87")

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Sample five camera poses
for i in range(5):
    # Sample random camera location around the object
    location = bproc.sampler.sphere([0, 0, 0], radius=2, mode="SURFACE")
    # Compute rotation based on vector going from location towards the location of the ShapeNet object
    rotation_matrix = bproc.camera.rotation_from_forward_vec(shapenet_obj.get_location() - location)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)

# render the whole pipeline
data = bproc.renderer.render()

# Collect the metadata of the shapenet object
shapenet_state = {
    "used_synset_id": shapenet_obj.get_cp("used_synset_id"),
    "used_source_id": shapenet_obj.get_cp("used_source_id")
}
# Add to the main data dict (its the same for all frames here)
data["shapenet_state"] = [shapenet_state] * bproc.utility.num_frames()

# Collect state of the camera at all frames
cam_states = []
for frame in range(bproc.utility.num_frames()):
    cam_states.append({
        "cam2world": bproc.camera.get_camera_pose(frame),
        "cam_K": bproc.camera.get_intrinsics_as_K_matrix()
    })
# Adds states to the data dict
data["cam_states"] = cam_states

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
