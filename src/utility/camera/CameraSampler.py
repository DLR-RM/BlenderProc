from typing import Callable, List

import bpy

from src.utility.CameraUtility import CameraUtility
from mathutils import Matrix

class CameraSampler:

    @staticmethod
    def sample(number_of_poses: int, sample_pose: Callable[[], Matrix] = None, is_pose_valid: Callable[[Matrix, List[Matrix]], bool] = None, max_tries=10000, on_new_pose_added: Callable[[Matrix, int], None] = None, on_max_tries_reached: Callable[[], bool] = None):
        """ Samples N valid camera poses.

        The sampling and validation procedure are specified via a function pointer.
        In each iteration a new camera pose is sampled via sample_pose() and only kept if is_pose_valid() returns True.
        This is done until N valid camera poses have been found or after max_tries has been reached.

        :param number_of_poses: The number of valid camera poses that should be sampled.
        :param sample_pose: The function that samples new camera poses in the form of a cam2world transformation matrix.
        :param is_pose_valid: The function that determines whether a sampled camera pose is a valid and should be kept.
        :param max_tries: The maximum number of tries before giving up.
        :param on_new_pose_added: A function that is called everytime a validated camera pose is permanently added.
        :param on_max_tries_reached: A function that is called if max_tries is reached. If this function then returns true, tries will be reset to 0 and the loop starts all over again.
        """
        # If not sample_pose function has been given, use a simple one that samples uniformly in SO(6)
        if sample_pose is None:
            sample_pose = lambda: None
        # If no is_pose_valid function has been given, use one that accepts all poses
        if is_pose_valid is None:
            is_pose_valid = lambda cam2world_matrix, existing_poses: True

        # Init
        all_tries = 0
        tries = 0
        existing_poses = []

        for i in range(number_of_poses):
            # Do until a valid pose has been found or the max number of tries has been reached
            while tries < max_tries:
                tries += 1
                all_tries += 1
                # Sample a new cam pose and check if its valid
                if CameraSampler.sample_and_validate_cam_pose(sample_pose, is_pose_valid, on_new_pose_added, existing_poses):
                    break

            # If max tries has been reached
            if tries >= max_tries and on_max_tries_reached is not None:
                # If callback returns True, start all over again.
                if on_max_tries_reached():
                    tries = 0

        print(str(all_tries) + " tries were necessary")

    @staticmethod
    def sample_and_validate_cam_pose(sample_pose: Callable[[], Matrix], is_pose_valid: Callable[[Matrix, List[Matrix]], bool], on_new_pose_added: Callable[[Matrix, int], None], existing_poses: [Matrix]):
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param sample_pose: The function that samples new camera poses in the form of a cam2world transformation matrix.
        :param is_pose_valid: The function that determines whether a sampled camera pose is a valid and should be kept.
        :param on_new_pose_added: A function that is called everytime a validated camera pose is permanently added.
        :param existing_poses: A list of already sampled valid poses.
        :return: True, if the sampled pose was valid
        """
        # Sample camera extrinsics (we do not set them yet for performance reasons)
        cam2world_matrix = sample_pose()

        if is_pose_valid(cam2world_matrix, existing_poses):
            # Set camera extrinsics as the pose is valid
            frame = CameraUtility.add_camera_pose(cam2world_matrix)
            # Optional callback
            if on_new_pose_added is not None:
                on_new_pose_added(cam2world_matrix, frame)
            # Add to the list of added cam poses
            existing_poses.append(cam2world_matrix)
            return True
        else:
            return False
