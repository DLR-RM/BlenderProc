from src.main.Module import Module
import mathutils
import bpy

from src.utility.Utility import Utility


class CameraLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        cam_ob = self.scene.camera
        cam = cam_ob.data

        # Open cam file, go through all poses and create key points
        with open(Utility.resolve_path(self.config.get_string("path"))) as f:
            camPoses = f.readlines()
            for i, camPos in enumerate(camPoses):
                camArgs = [float(x) for x in camPos.strip().split()]
                cam_ob.location = mathutils.Vector([camArgs[0], -camArgs[2], camArgs[1]])

                rot_quat = mathutils.Vector([camArgs[3], -camArgs[5], camArgs[4]]).to_track_quat('-Z', 'Y')
                cam_ob.rotation_euler = rot_quat.to_euler()
                cam.lens_unit = 'FOV'
                cam.angle = camArgs[9] * 2
                cam.clip_start = 1
                cam_ob.keyframe_insert(data_path='location', frame=i + 1)
                cam_ob.keyframe_insert(data_path='rotation_euler', frame=i + 1)
            bpy.data.scenes["Scene"].frame_end = len(camPoses)