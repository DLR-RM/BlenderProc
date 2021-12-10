import blenderproc as bproc
import argparse
import bpy

parser = argparse.ArgumentParser()
parser.add_argument('urdf_file', nargs='?', default="./model.urdf", help="Path to the .urdf file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/urdf_loading_and_manipulation/output", help="Path to where the final files will be saved")
args = parser.parse_args()

bproc.init()

robot = bproc.loader.load_robot(urdf_file=args.urdf_file)

robot.hide_irrelevant_objs()
robot.remove_link_by_index(index=0)
robot.set_ascending_category_ids()

# rotate for some parts
robot_matrix_world = []
for frame in range(9):
    for link in robot.links:
        if link.joint_type == "revolute":
            link.set_rotation_euler(rotation_euler=0.1, mode="relative", frame=frame)
    if frame > bpy.context.scene.frame_end:
        bpy.context.scene.frame_end += 1
    robot_matrix_world.append(robot.get_all_local2world_mats())

# set a light source
light = bproc.types.Light()
light.set_type(type="POINT")
light.set_location(location=[5, 5, 5])
light.set_energy(energy=1000)

# sample camera pose
bproc.camera.set_intrinsics_from_blender_params(640, 480)
location = [-1., 2., 2.]
poi = bproc.object.compute_poi(robot.links[1].get_visuals())
# Compute rotation based on vector going from location towards poi
rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=3.14)
# Add homog cam pose based on location and rotation
cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
bproc.camera.add_camera_pose(cam2world_matrix)
# render RGB images
data = bproc.renderer.render()

# render segmentation images
data.update(bproc.renderer.render_segmap(use_alpha_channel=True))

# write the data to a .hdf5 container
data['robot_matrix_world'] = robot_matrix_world
bproc.writer.write_hdf5(args.output_dir, data)
