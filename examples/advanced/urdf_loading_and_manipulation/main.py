import blenderproc as bproc
import argparse
import numpy as np
import cv2
import os

from blenderproc.python.writer.BopWriterUtility import BopWriterUtility

parser = argparse.ArgumentParser()
parser.add_argument('urdf_file', nargs='?', default="./model.urdf", help="Path to the .urdf file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/urdf_loading_and_manipulation/output", help="Path to where the final files will be saved")
args = parser.parse_args()

bproc.init()


robot = bproc.loader.load_urdf(urdf_file=args.urdf_file)

robot.hide_irrelevant_objs()
robot.remove_link_by_index(index=0)
robot.set_ascending_category_ids()


# rotate for some parts
# 1,2,3,5,6,8,9,16,17,19,20
# child link frame = joint frame
# robot_fk_joint_angles = []
# out = cv2.VideoWriter(os.path.join(args.output_dir, 'miro.avi'),cv2.VideoWriter_fourcc(*'DIVX'), 15, (1280, 960))
# for frame in range(10):
#     for i,link in enumerate(robot.links):
#         if link.joint_type == "revolute":
#             if 'link6' in link.get_name():
#                 joint_angle = 4.5+np.sin(3*np.pi/150*frame)
#             else:
#                 joint_angle = np.sin(3*np.pi/150*0.2*frame)
#             robot.set_rotation_euler_fk(link, rotation_euler=joint_angle, mode="absolute", frame=frame)
#     robot_fk_joint_angles.append([j.get_joint_rotation(frame=frame) for j in robot.get_revolute_joints()])
    
    
from blenderproc.python.types.BoneUtility import set_copy_rotation_constraint, add_constraint_if_not_existing

for link in robot.links:
    if link.get_name() == 'link1_right_visual':
        break
robot.create_ik_bone_controller(link=link, relative_location=[0., 0., 0.])

# add copy transforms constraints
bones_to_add_constraints = ['finger_right_joint_virtual1.ik', 'link2_right_joint.ik', 'lever_right_joint.ik']

for bone_name in bones_to_add_constraints:
    bone = robot.blender_obj.pose.bones.get(bone_name)
    c = add_constraint_if_not_existing(bone, constraint_name='Copy Rotation')
    c.target = robot.blender_obj
    c.subtarget = 'link1_right_joint.ik'
    c.target_space = 'POSE'
    c.owner_space = 'POSE'
    # only necessary for the pose bone in the copy rotation loop below, but good practice
    bone.constraints.move(len(bone.constraints) - 1, 0)

# add copy rotation constraints for mimicing movement on the opposite side
# would also work with set_copy_rotation_constraint
bones_to_add_constraints = ['finger_left_joint.ik', 'finger_left_joint_virtual1.ik', 'link2_left_joint.ik',
                            'lever_left_joint.ik', 'link1_left_joint.ik']

for bone_name in bones_to_add_constraints:
    bone = robot.blender_obj.pose.bones.get(bone_name)
    c = add_constraint_if_not_existing(bone, constraint_name='Copy Rotation')
    c.target = robot.blender_obj
    c.subtarget = bone_name.replace('left', 'right')
    if bone_name == 'finger_left_joint.ik':
        c.target_space = 'POSE'
        c.owner_space = 'POSE'
    else:
        c.target_space = 'LOCAL'
        c.owner_space = 'LOCAL'
    bone.constraints.move(len(bone.constraints) - 1, 0)

# add ik limit
bone = robot.blender_obj.pose.bones.get('link1_right_joint.ik')
bone.use_ik_limit_y = True
bone.ik_min_y = -0.823795  # -47.3°
bone.ik_max_y = 0.


for i in range(10):
    robot.set_location_ik(location=[0.05*np.sin(i/5 * np.pi % np.pi), 0., 0.0575], frame=i)
    if robot.has_reached_ik_pose(location_error=0.01, rotation_error=0.01):
        print("Robot has reached pose!")
    else:
        print("Robot has not reached pose")




# Set a random hdri from the given haven directory as background
# haven_hdri_path = bproc.loader.get_random_world_background_hdr_img_path_from_haven('/volume/reconstruction_data/datasets/haven_dataset/')
# bproc.world.set_world_background_hdr_img(haven_hdri_path)
bproc.world.set_world_background_hdr_img('/home/msundermeyer/Downloads/surgery_8k.hdr')

# set a light source
light = bproc.types.Light()
light.set_type(type="POINT")
light.set_location(location=[5, 5, 5])
light.set_energy(energy=1000)

# sample camera pose
bproc.camera.set_intrinsics_from_K_matrix(np.array([[1000, 0, 640],
                                                    [0, 1000, 480], 
                                                    [0, 0, 1]]), 1280, 960)

location = [0.8, 1.5, 1.3]
poi = bproc.object.compute_poi(robot.links[1].visuals) + np.array([0., 0., 0.3])
# Compute rotation based on vector going from location towards poi
rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location)
# Add homog cam pose based on location and rotation
cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
bproc.camera.add_camera_pose(cam2world_matrix)
# render RGB images
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.set_max_amount_of_samples(50)


data = bproc.renderer.render()


out = cv2.VideoWriter(os.path.join(args.output_dir, 'miro.avi'),cv2.VideoWriter_fourcc(*'DIVX'), 15, (1280, 960))
for frame in data["colors"]:
    bgr = cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)
    out.write(bgr)
    cv2.imshow('bgr', bgr)
    cv2.waitKey(0)

bproc.writer.write_bop(os.path.join(args.output_dir, 'bop_data'), 
                        target_objects = robot.links[1:],
                        depths = data["depth"],
                        colors = data["colors"], 
                        m2mm = False,
                        color_file_format = "PNG")
# print(robot_fk_joint_angles)
# BopWriterUtility._save_json(os.path.join(args.output_dir, 'bop_data', 'robot_fk_joint_angles.json'), robot_fk_joint_angles)

# # Release everything if job is finished
out.release()
cv2.destroyAllWindows()