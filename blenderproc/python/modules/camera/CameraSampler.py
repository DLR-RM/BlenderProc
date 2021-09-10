import sys
from typing import List
import numpy as np

import bpy

from blenderproc.python.modules.camera.CameraInterface import CameraInterface
from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects
import blenderproc.python.camera.CameraUtility as CameraUtility
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.modules.utility.ItemCollection import ItemCollection
from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes, create_bvh_tree_multi_objects, \
    scene_ray_cast
import blenderproc.python.camera.CameraValidation as CameraValidation

class CameraSampler(CameraInterface):
    """
    A general camera sampler.

    First a camera pose is sampled according to the configuration, then it is checked if the pose is valid.
    If that's not the case a new camera pose is sampled instead.

    Supported cam pose validation methods:
    - Checking if the distance to objects is in a configured range
    - Checking if the scene coverage/interestingness score is above a configured threshold
    - Checking if a candidate pose is sufficiently different than the sampled poses so far

    Example 1: Sampling 10 camera poses.

    .. code-block:: yaml

        {
          "module": "camera.SuncgCameraSampler",
          "config": {
            "cam_poses": [
            {
              "number_of_samples": 10,
              "proximity_checks": {
                "min": 1.0
              },
              "min_interest_score": 0.4,
              "location": {
                "provider":"sampler.Uniform3d",
                "max":[0, 0, 2],
                "min":[0, 0, 0.5]
              },
              "rotation": {
                "value": {
                  "provider":"sampler.Uniform3d",
                  "max":[1.2217, 0, 6.283185307],
                  "min":[1.2217, 0, 0]
                }
              }
            }
            ]
          }
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - intrinsics
          - A dict which contains the intrinsic camera parameters. Check CameraInterface for more info. Default:
            {}.
          - dict
        * - cam_poses
          - Camera poses configuration list. Each cell contains a separate config data.
          - list
        * - default_cam_param
          - A dict which can be used to specify properties across all cam poses. Check CameraInterface for more
            info. Default: {}.
          - dict

    **Properties per cam pose**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - number_of_samples
          - The number of camera poses that should be sampled. Note depending on some constraints (e.g. interest
            scores), the sampler might not return all of the camera poses if the number of tries exceeded the
            configured limit. Default: 1.
          - int
        * - max_tries
          - The maximum number of tries that should be made to sample the requested number of cam poses per interest
            score. Default: 10000.
          - int
        * - sqrt_number_of_rays
          - The square root of the number of rays which will be used to determine, if there is an obstacle in front
            of the camera. Default: 10.
          - int
        * - proximity_checks
          - A dictionary containing operators (e.g. avg, min) as keys and as values dictionaries containing
            thresholds in the form of {"min": 1.0, "max":4.0} or just the numerical threshold in case of max or min.
            The operators are combined in conjunction (i.e boolean AND). This can also be used to avoid the
            background in images, with the no_background: True option. Default: {}.
          - dict
        * - excluded_objs_in_proximity_check
          - A list of objects, returned by getter.Entity to remove some objects from the proximity checks defined in
            'proximity_checks'. Default: []
          - list
        * - min_interest_score
          - Arbitrary threshold to discard cam poses with less interesting views. Default: 0.0.
          - float
        * - interest_score_range
          - The maximum of the range of interest scores that would be used to sample the camera poses. Interest
            score range example: min_interest_score = 0.8, interest_score_range = 1.0, interest_score_step = 0.1
            interest score list = [1.0, 0.9, 0.8]. The sampler would reject any pose with score less than 1.0. If
            max tries is reached, it would switch to 0.9 and so on. min_interest_score = 0.8, interest_score_range =
            0.8, interest_score_step = 0.1 (or any value bigger than 0) interest score list = [0.8]. Default:
            min_interest_score.
          - float
        * - interest_score_step
          - Step size for the list of interest scores that would be tried in the range from min_interest_score to
            interest_score_range. Must be bigger than 0. " Default: 0.1.
          - float
        * - special_objects
          - Objects that weights differently in calculating whether the scene is interesting or not, uses the
            coarse_grained_class or if not SUNCG, 3D Front, the category_id. Default: [].
          - list
        * - special_objects_weight
          - Weighting factor for more special objects, used to estimate the interestingness of the scene. Default:
            2.0.
          - float
        * - check_pose_novelty_rot
          - Checks that a sampled new pose is novel with respect to the rotation component. Default: False
          - bool
        * - check_pose_novelty_translation
          - Checks that a sampled new pose is novel with respect to the translation component. Default: False.
          - bool
        * - min_var_diff_rot
          - Considers a pose novel if it increases the variance of the rotation component of all poses sampled by
            this parameter's value in percentage. If set to -1, then it would only check that the variance is
            increased. Default: sys.float_info.min.
          - float
        * - min_var_diff_translation
          - Same as min_var_diff_rot but for translation. If set to -1, then it would only check that the variance
            is increased. Default: sys.float_info.min.
          - float
        * - check_if_pose_above_object_list
          - A list of objects, where each camera has to be above, could be the floor or a table. Default: [].
          - list
        * - check_if_objects_visible
          - A list of objects, which always should be visible in the camera view. Default: [].
          - list
    """

    def __init__(self, config):
        CameraInterface.__init__(self, config)
        self.bvh_tree = None

        self.rotations = []
        self.translations = []

        self.var_rot, self.var_translation = 0.0, 0.0
        self.check_pose_novelty_rot = self.config.get_bool("check_pose_novelty_rot", False)
        self.check_pose_novelty_translation = self.config.get_bool("check_pose_novelty_translation", False)

        self.min_var_diff_rot = self.config.get_float("min_var_diff_rot", sys.float_info.min)
        if self.min_var_diff_rot == -1.0:
            self.min_var_diff_rot = sys.float_info.min

        self.min_var_diff_translation = self.config.get_float("min_var_diff_translation", sys.float_info.min)
        if self.min_var_diff_translation == -1.0:
            self.min_var_diff_translation = sys.float_info.min

        self.cam_pose_collection = ItemCollection(self._sample_cam_poses, self.config.get_raw_dict("default_cam_param", {}))

    def run(self):
        """ Sets camera poses. """

        source_specs = self.config.get_list("cam_poses")
        for i, source_spec in enumerate(source_specs):
            self.cam_pose_collection.add_item(source_spec)

    def _sample_cam_poses(self, config):
        """ Samples camera poses according to the given config

        :param config: The config object
        """
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        # Set global parameters
        self.sqrt_number_of_rays = config.get_int("sqrt_number_of_rays", 10)
        self.max_tries = config.get_int("max_tries", 10000)
        self.proximity_checks = config.get_raw_dict("proximity_checks", {})
        self.excluded_objects_in_proximity_check = config.get_list("excluded_objs_in_proximity_check", [])
        self.min_interest_score = config.get_float("min_interest_score", 0.0)
        self.interest_score_range = config.get_float("interest_score_range", self.min_interest_score)
        self.interest_score_step = config.get_float("interest_score_step", 0.1)
        self.special_objects = config.get_list("special_objects", [])
        self.special_objects_weight = config.get_float("special_objects_weight", 2)
        self._above_objects = convert_to_meshes(config.get_list("check_if_pose_above_object_list", []))
        self.check_visible_objects = convert_to_meshes(config.get_list("check_if_objects_visible", []))

        # Set camera intrinsics
        self._set_cam_intrinsics(cam, Config(self.config.get_raw_dict("intrinsics", {})))

        if self.proximity_checks:
            # needs to build an bvh tree
            mesh_objects = [MeshObject(obj) for obj in get_all_blender_mesh_objects() if obj not in self.excluded_objects_in_proximity_check]
            self.bvh_tree = create_bvh_tree_multi_objects(mesh_objects)

        if self.interest_score_step <= 0.0:
            raise Exception("Must have an interest score step size bigger than 0")

        # Determine the number of camera poses to sample
        number_of_poses = config.get_int("number_of_samples", 1)
        print("Sampling " + str(number_of_poses) + " cam poses")

        # Start with max interest score
        self.interest_score = self.interest_score_range

        # Init
        all_tries = 0
        tries = 0
        existing_poses = []

        for i in range(number_of_poses):
            # Do until a valid pose has been found or the max number of tries has been reached
            while tries < self.max_tries:
                tries += 1
                all_tries += 1
                # Sample a new cam pose and check if its valid
                if self.sample_and_validate_cam_pose(config, existing_poses):
                    break

            # If max tries has been reached
            if tries >= self.max_tries:
                # Decrease interest score and try again, if we have not yet reached minimum
                continue_trying, self.interest_score = CameraValidation.decrease_interest_score(self.interest_score, self.min_interest_score, self.interest_score_step)
                if continue_trying:
                    tries = 0

        print(str(all_tries) + " tries were necessary")

    def sample_and_validate_cam_pose(self, config: Config, existing_poses: List[np.ndarray]) -> bool:
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param config: The config object describing how to sample
        :param existing_poses: A list of already sampled valid poses.
        :return: True, if the sampled pose was valid
        """
        # Sample camera extrinsics (we do not set them yet for performance reasons)
        cam2world_matrix = self._sample_pose(config)

        if self._is_pose_valid(cam2world_matrix, existing_poses):
            # Set camera extrinsics as the pose is valid
            frame = CameraUtility.add_camera_pose(cam2world_matrix)
            # Optional callback
            self._on_new_pose_added(cam2world_matrix, frame)
            # Add to the list of added cam poses
            existing_poses.append(cam2world_matrix)
            return True
        else:
            return False

    def _on_new_pose_added(self, cam2world_matrix: np.ndarray, frame: int):
        """
        :param cam2world_matrix: The new camera pose.
        :param frame: The frame containing the new pose.
        """
        pass

    def _sample_pose(self, config) -> np.ndarray:
        """
        :return: The new sampled pose.
        """
        cam2world_matrix = self._cam2world_matrix_from_cam_extrinsics(config)
        return cam2world_matrix

    def _is_pose_valid(self, cam2world_matrix: np.ndarray, existing_poses: List[np.ndarray]) -> bool:
        """ Determines if the given pose is valid.

        - Checks if the distance to objects is in the configured range
        - Checks if the scene coverage score is above the configured threshold

        :param cam2world_matrix: The sampled camera extrinsics in form of a camera to world frame transformation matrix.
        :param existing_poses: The list of already sampled valid poses.
        :return: True, if the pose is valid
        """
        if not CameraValidation.perform_obstacle_in_view_check(cam2world_matrix, self.proximity_checks, self.bvh_tree, self.sqrt_number_of_rays):
            return False

        if self.interest_score > 0 and CameraValidation.scene_coverage_score(cam2world_matrix, self.special_objects, self.special_objects_weight, self.sqrt_number_of_rays) < self.interest_score:
            return False

        if len(self.check_visible_objects) > 0:
            visible_objects = CameraValidation.visible_objects(cam2world_matrix, self.sqrt_number_of_rays)
            for obj in self.check_visible_objects:
                if obj not in visible_objects:
                    return False

        if not CameraValidation.check_novel_pose(cam2world_matrix, existing_poses, self.check_pose_novelty_rot, self.check_pose_novelty_translation, self.min_var_diff_rot, self.min_var_diff_translation):
            return False

        if self._above_objects:
            _, _, _, _, hit_object, _ = scene_ray_cast(cam2world_matrix[:3, 3], [0, 0, -1])
            if hit_object not in self._above_objects:
                return False

        return True
