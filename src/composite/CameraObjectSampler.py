import bpy

from src.main.Module import Module
from src.utility.BlenderUtility import get_all_blender_mesh_objects
from src.utility.Utility import Utility


class CameraObjectSampler(Module):
    """ Alternates between sampling new cameras using camera.CameraSampler and sampling new object poses using object.ObjectPoseSampler

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - total_noof_cams
          - Total number of sampled cameras. Default: 10
          - int
        * - noof_cams_per_scene
          - Number of sampled cameras after which object poses are re-sampled. Default: 5
          - int
        * - object_pose_sampler
          - The config module based on the object.ObjectPoseSampler Default: {}
          - dict
        * - camera_pose_sampler
          - The config module based on the camera.CameraSampler Default: {}
          - dict
    """

    def __init__(self, config):
        Module.__init__(self, config)

        object_pose_sampler_config = config.get_raw_dict("object_pose_sampler", {})
        camera_pose_sampler_config = config.get_raw_dict("camera_pose_sampler", {})

        self._object_pose_sampler = Utility.initialize_modules([object_pose_sampler_config])[0]
        self._camera_pose_sampler = Utility.initialize_modules([camera_pose_sampler_config])[0]
    
    def run(self):
        total_noof_cams = self.config.get_int("total_noof_cams", 10)
        noof_cams_per_scene = self.config.get_int("noof_cams_per_scene", 5)

        for i in range(total_noof_cams):
            if i % noof_cams_per_scene == 0:
                # sample new object poses
                self._object_pose_sampler.run()

            # get current keyframe id
            frame_id = bpy.context.scene.frame_end

            # TODO: Use Getter for selecting objects
            for obj in get_all_blender_mesh_objects():
                # insert keyframes for current object poses
                self._object_pose_sampler.insert_key_frames(obj, frame_id)

            # sample new camera poses
            self._camera_pose_sampler.run()
