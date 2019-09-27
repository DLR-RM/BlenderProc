from src.camera.CameraModule import CameraModule
from src.main.Module import Module
import mathutils
import bpy

from src.utility.Utility import Utility


class SuncgCameraLoader(CameraModule):

    def __init__(self, config):
        CameraModule.__init__(self, config)

    def run(self):
        """ Loads camera poses from the configured suncg camera file and sets them as separate keypoints.

        Layout of the camera pose file should be:
        eyeX eyeY eyeZ forwardX forwardY forwardZ upX upY upZ fovX fovY
        """
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        # Open cam file, go through all poses and create key points
        with open(Utility.resolve_path(self.config.get_string("path"))) as f:
            camPoses = f.readlines()
            # remove all empty lines
            camPoses = [line for line in camPoses if len(line.strip()) > 3]
            for i, camPos in enumerate(camPoses):
                camArgs = [float(x) for x in camPos.strip().split()]
                print('----------------')
                print(", ".join(["{:1.4}".format(ele) for ele in camArgs]))
                for i in range(3,6):
                    import math
                    camArgs[i] = camArgs[i] / math.sqrt(camArgs[3] * camArgs[3] + camArgs[4] * camArgs[4] + camArgs[5] * camArgs[5])
                print(", ".join(["{:1.4}".format(ele) for ele in camArgs]))

                # Fix coordinate frame (blender and suncg use different ones)
                def convertToBlender(vec):
                    return mathutils.Vector([vec[0], -vec[2], vec[1]])

                cam_ob.location = convertToBlender(camArgs[:3])
                rot_quat = convertToBlender(camArgs[3:6]).to_track_quat('-Z', 'Y')
                cam_ob.rotation_euler = rot_quat.to_euler()

                cam.lens_unit = 'FOV'
                cam.angle = camArgs[9] * 2
                cam.clip_start = self.config.get_float("near_clipping", 1)
                cam_ob.keyframe_insert(data_path='location', frame=i + 1)
                cam_ob.keyframe_insert(data_path='rotation_euler', frame=i + 1)

                self._write_cam_pose_to_file(i + 1, cam, cam_ob, suncg_version=True)

            bpy.context.scene.frame_end = len(camPoses)
            self._register_cam_pose_output()