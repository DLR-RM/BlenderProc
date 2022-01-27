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

# Set a random hdri from the given haven directory as background
# haven_hdri_path = bproc.loader.get_random_world_background_hdr_img_path_from_haven('/volume/reconstruction_data/datasets/haven_dataset/')
# bproc.world.set_world_background_hdr_img(haven_hdri_path)
bproc.world.set_world_background_hdr_img('resources/machine_shop_01_8k.hdr')

robot = bproc.loader.load_urdf(urdf_file=args.urdf_file)

robot.set_ascending_category_ids()
breakpoint()

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

# rotate for some parts
# 1,2,3,5,6,8,9,16,17,19,20
# child link frame = joint frame
robot_joint_angles = []
out = cv2.VideoWriter(os.path.join(args.output_dir, 'miro.avi'),cv2.VideoWriter_fourcc(*'DIVX'), 15, (1280, 960))
for frame in range(20):
    for i,link in enumerate(robot.links):
        if link.joint_type == "revolute":
            if 'link6' in link.get_name():
                link.set_rotation_euler_fk(rotation_euler=4.5+np.sin(3*np.pi/10*frame), mode="absolute")
            else:
                link.set_rotation_euler_fk(rotation_euler=np.sin(3*np.pi/10*0.2*frame), mode="absolute")

    robot_joint_angles.append([angle for angle in robot.get_all_joint_angles()])

    data = bproc.renderer.render()
    

    bgr = cv2.cvtColor(data["colors"][0],cv2.COLOR_RGB2BGR)
    cv2.imshow('bgr', bgr)
    cv2.waitKey(0)
    out.write(bgr)

    breakpoint()
    
    bproc.writer.write_bop(os.path.join(args.output_dir, 'bop_data'), 
                            target_objects = robot.links[2:],
                            depths = data["depth"],
                            colors = data["colors"], 
                            m2mm = False,
                            color_file_format = "PNG")

BopWriterUtility._save_json(os.path.join(args.output_dir, 'bop_data', 'robot_joint_angles.json'), robot_joint_angles)
out.release()

