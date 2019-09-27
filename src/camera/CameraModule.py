from src.main.Module import Module
import mathutils
import bpy
import numpy as np
import os

class CameraModule(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def _write_cam_pose_to_file(self, frame, cam, cam_ob, room_id=-1, suncg_version=False):
        """ Determines the current pose of the given camera and writes it to a .npy file.

        :param frame: The current frame number, used for naming the output file.
        :param cam: The camera.
        :param cam_ob: The camera object.
        :param room_id: The id of the room which contains the camera (optional)
        """
        cam_pose = []
        if suncg_version:
            # Fix coordinate frame (blender and suncg use different ones)
            def convertToSuncg(vec):
                return [vec[0], vec[2], -vec[1]]
            # Location
            cam_pose.extend(convertToSuncg(cam_ob.location[:]))
            # convert euler angle to a direction vector
            rot_mat = cam_ob.rotation_euler.to_matrix()
            towards = rot_mat @ mathutils.Vector([0,0,1])
            cam_pose.extend(convertToSuncg(towards))
            up = rot_mat @ mathutils.Vector([0,1,0])
            cam_pose.extend(convertToSuncg(up))
            # FOV
            cam_pose.extend([cam.angle_x*0.5, cam.angle_y*0.5])

        else:
            # Location
            cam_pose.extend(cam_ob.location[:])
            # Orientation
            cam_pose.extend(cam_ob.rotation_euler[:])
            # FOV
            cam_pose.extend([cam.angle_x, cam.angle_y])
            # Room
            cam_pose.append(room_id)
        # print(", ".join(["{:1.4}".format(float(ele)) for ele in cam_pose]))
        # def convertToBlender(vec):
        #     return mathutils.Vector([vec[0], -vec[2], vec[1]])
        # towards = convertToBlender(cam_pose[3:6])
        # up = convertToBlender(cam_pose[6:9])
        # zaxis = towards * -1
        # xaxis = up.cross(zaxis).normalized()
        # yaxis = zaxis.cross(xaxis).normalized()
        # print(", ".join(["{:1.4}".format(float(ele)) for ele in zaxis]) + ', ' + ", ".join(["{:1.4}".format(float(ele)) for ele in yaxis]))
        # print(", ".join(["{:1.4}".format(float(ele)) for ele in cam_pose[3:6]]) + ', ' + ", ".join(["{:1.4}".format(float(ele)) for ele in cam_pose[6:9]]))
        np.save(os.path.join(self.output_dir, "campose_" + ("%04d" % frame)), cam_pose)

    def _register_cam_pose_output(self):
        """ Registers the written cam pose files as an output """
        self._register_output("campose_", "campose", ".npy", "1.0.0")