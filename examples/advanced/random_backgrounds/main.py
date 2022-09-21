import blenderproc as bproc
import numpy as np
import argparse
import random
import os

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/advanced/random_backgrounds/object.ply", help="Path to the object file.")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/random_backgrounds/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
obj = bproc.loader.load_obj(args.scene)[0]
obj.set_cp("category_id", 1)

# Randomly perturbate the material of the object
mat = obj.get_materials()[0]
mat.set_principled_shader_value("Specular", random.uniform(0, 1))
mat.set_principled_shader_value("Roughness", random.uniform(0, 1))
mat.set_principled_shader_value("Base Color", np.random.uniform([0, 0, 0, 1], [1, 1, 1, 1]))
mat.set_principled_shader_value("Metallic", random.uniform(0, 1))

# Create a new light
light = bproc.types.Light()
light.set_type("POINT")
# Sample its location around the object
light.set_location(bproc.sampler.shell(
    center=obj.get_location(),
    radius_min=1,
    radius_max=5,
    elevation_min=1,
    elevation_max=89
))
# Randomly set the color and energy
light.set_color(np.random.uniform([0.5, 0.5, 0.5], [1, 1, 1]))
light.set_energy(random.uniform(100, 1000))

bproc.camera.set_resolution(640, 480)

# Sample five camera poses
poses = 0
tries = 0
while tries < 10000 and poses < 5:
    # Sample random camera location around the object
    location = bproc.sampler.shell(
        center=obj.get_location(),
        radius_min=1,
        radius_max=4,
        elevation_min=1,
        elevation_max=89
    )
    # Compute rotation based lookat point which is placed randomly around the object
    lookat_point = obj.get_location() + np.random.uniform([-0.5, -0.5, -0.5], [0.5, 0.5, 0.5])
    rotation_matrix = bproc.camera.rotation_from_forward_vec(lookat_point - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)

    # Only add camera pose if object is still visible
    if obj in bproc.camera.visible_objects(cam2world_matrix):
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# Enable transparency so the background becomes transparent
bproc.renderer.set_output_format(enable_transparency=True)
# add segmentation masks (per class and per instance)
bproc.renderer.enable_segmentation_output(map_by=["category_id", "instance", "name"])

# Render RGB images
data = bproc.renderer.render()

# Write data to coco file
bproc.writer.write_coco_annotations(os.path.join(args.output_dir, 'coco_data'),
                                    instance_segmaps=data["instance_segmaps"],
                                    instance_attribute_maps=data["instance_attribute_maps"],
                                    colors=data["colors"],
                                    append_to_existing_output=True)
