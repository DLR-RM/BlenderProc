import blenderproc as bproc
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('model', nargs='?', default="resources/haven/models/ArmChair_01/ArmChair_01_2k.blend", help="ath to the blend file, from the haven dataset, browse the model folder, for all possible options")
parser.add_argument('hdri_path', nargs='?', default="resources/haven", help="The folder where the `hdri` folder can be found, to load an world environment")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/haven/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
obj = bproc.loader.load_blend(args.model)[0]

haven_hdri_path = bproc.loader.get_random_world_background_hdr_img_path_from_haven(args.hdri_path)
bproc.world.set_world_background_hdr_img(haven_hdri_path)

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# Sample five camera poses
for i in range(5):
    # Sample random camera location above objects
    location = bproc.sampler.part_sphere(center=np.array([0, 0, 0]), mode="SURFACE", radius=3, part_sphere_dir_vector=np.array([1, 0, 0]), dist_above_center=0.5)
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(obj.get_location() - location)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)

# Add dust to all materials of the loaded object
for material in obj.get_materials():
    bproc.material.add_dust(material, strength=0.8, texture_scale=0.05)

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
