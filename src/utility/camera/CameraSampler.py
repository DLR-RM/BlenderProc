import bpy

from src.utility.CameraUtility import CameraUtility


class CameraSampler:

    @staticmethod
    def sample(number_of_poses, sample_pose=None, is_pose_valid=None, max_tries=100000000, on_max_tries_reached=None):
        """ Sets camera poses. """

        if sample_pose is None:
            sample_pose = lambda: None
        if is_pose_valid is None:
            is_pose_valid = lambda cam, cam_ob, cam2world_matrix: True

        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        all_tries = 0  # max_tries is now applied per each score
        tries = 0

        for i in range(number_of_poses):
            # Do until a valid pose has been found or the max number of tries has been reached
            while tries < max_tries:
                tries += 1
                all_tries += 1
                # Sample a new cam pose and check if its valid
                if CameraSampler.sample_and_validate_cam_pose(cam, cam_ob, sample_pose, is_pose_valid):
                    break

            if tries >= max_tries and on_max_tries_reached is not None:
                if on_max_tries_reached():
                    tries = 0

        print(str(all_tries) + " tries were necessary")

    @staticmethod
    def sample_and_validate_cam_pose(cam, cam_ob, sample_pose, is_pose_valid):
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: The config object describing how to sample
        :return: True, if the sampled pose was valid
        """
        # Sample camera extrinsics (we do not set them yet for performance reasons)
        cam2world_matrix = sample_pose()

        if is_pose_valid(cam, cam_ob, cam2world_matrix):
            # Set camera extrinsics as the pose is valid
            CameraUtility.add_camera_pose(cam2world_matrix)
            return True
        else:
            return False
