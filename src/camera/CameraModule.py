from src.main.Module import Module
import mathutils
import bpy
import numpy as np
import os

class CameraModule(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def _write_cam_pose_to_file(self, frame, cam, cam_ob, room_id=-1):
        """ Determines the current pose of the given camera and writes it to a .npy file.

        :param frame: The current frame number, used for naming the output file.
        :param cam: The camera.
        :param cam_ob: The camera object.
        :param room_id: The id of the room which contains the camera (optional)
        """
        cam_pose = []
        # Location
        cam_pose.extend(cam_ob.location[:])
        # Orientation
        cam_pose.extend(cam_ob.rotation_euler[:])
        # FOV
        cam_pose.extend([cam.angle_x, cam.angle_y])
        # Room
        cam_pose.append(room_id)
        np.save(os.path.join(self.output_dir, "campose_" + ("%04d" % frame)), cam_pose)

    def _register_cam_pose_output(self):
        """ Registers the written cam pose files as an output """
        self._register_output("campose_", "campose", ".npy")