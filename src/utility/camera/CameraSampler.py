import numbers
import sys
from collections import defaultdict

import bmesh
import bpy
import mathutils
import numpy as np

from src.camera.CameraInterface import CameraInterface
from src.utility.CameraUtility import CameraUtility
from src.utility.BlenderUtility import get_all_blender_mesh_objects
from src.utility.Config import Config
from src.utility.ItemCollection import ItemCollection


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
            score. Default: 100000000.
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

        self.var_rot, self.var_translation   = 0.0, 0.0
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
        self._is_bvh_tree_inited = False
        self.sqrt_number_of_rays = config.get_int("sqrt_number_of_rays", 10)
        self.max_tries = config.get_int("max_tries", 100000000)
        self.proximity_checks = config.get_raw_dict("proximity_checks", {})
        self.excluded_objects_in_proximity_check = config.get_list("excluded_objs_in_proximity_check", [])
        self.min_interest_score = config.get_float("min_interest_score", 0.0)
        self.interest_score_range = config.get_float("interest_score_range", self.min_interest_score)
        self.interest_score_step = config.get_float("interest_score_step", 0.1)
        self.special_objects = config.get_list("special_objects", [])
        self.special_objects_weight = config.get_float("special_objects_weight", 2)
        self._above_objects = config.get_list("check_if_pose_above_object_list", [])
        self.check_visible_objects = config.get_list("check_if_objects_visible", [])

        # Set camera intrinsics
        self._set_cam_intrinsics(cam, Config(self.config.get_raw_dict("intrinsics", {})))

        if self.proximity_checks:
            # needs to build an bvh tree
            self._init_bvh_tree()

        if self.interest_score_step <= 0.0:
            raise Exception("Must have an interest score step size bigger than 0")

        # Determine the number of camera poses to sample
        number_of_poses = config.get_int("number_of_samples", 1)
        print("Sampling " + str(number_of_poses) + " cam poses")

        if self.min_interest_score == self.interest_score_range:
            step_size = 1
        else:    
            step_size = (self.interest_score_range - self.min_interest_score) / self.interest_score_step
            step_size += 1  # To include last value
        # Decreasing order
        interest_scores = np.linspace(self.interest_score_range, self.min_interest_score, step_size)
        score_index = 0

        all_tries = 0  # max_tries is now applied per each score
        tries = 0

        self.min_interest_score = interest_scores[score_index]
        print("Trying a min_interest_score value: %f" % self.min_interest_score)
        for i in range(number_of_poses):
            # Do until a valid pose has been found or the max number of tries has been reached
            while tries < self.max_tries:
                tries += 1
                all_tries += 1
                # Sample a new cam pose and check if its valid
                if self.sample_and_validate_cam_pose(cam, cam_ob, config):
                    break

            if tries >= self.max_tries:
                if score_index == len(interest_scores) - 1:  # If we tried all score values
                    print("Maximum number of tries reached!")
                    break
                # Otherwise, try a different lower score and reset the number of trials
                score_index += 1
                self.min_interest_score = interest_scores[score_index]
                print("Trying a different min_interest_score value: %f" % self.min_interest_score)
                tries = 0

        print(str(all_tries) + " tries were necessary")

    def sample_and_validate_cam_pose(self, cam, cam_ob, config):
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: The config object describing how to sample
        :return: True, if the sampled pose was valid
        """
        # Sample camera extrinsics (we do not set them yet for performance reasons)
        cam2world_matrix = self._cam2world_matrix_from_cam_extrinsics(config)

        if self._is_pose_valid(cam, cam_ob, cam2world_matrix):
            # Set camera extrinsics as the pose is valid
            CameraUtility.add_camera_pose(cam2world_matrix)
            return True
        else:
            return False

    def _is_pose_valid(self, cam, cam_ob, cam2world_matrix):
        """ Determines if the given pose is valid.

        - Checks if the distance to objects is in the configured range
        - Checks if the scene coverage score is above the configured threshold

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param cam2world_matrix: The sampled camera extrinsics in form of a camera to world frame transformation matrix.
        :return: True, if the pose is valid
        """
        if not self._perform_obstacle_in_view_check(cam, cam2world_matrix):
            return False

        if self.min_interest_score > 0 and self._scene_coverage_score(cam, cam2world_matrix) < self.min_interest_score:
            return False

        if len(self.check_visible_objects) > 0:
            visible_objects = self._visible_objects(cam, cam2world_matrix)
            for obj in self.check_visible_objects:
                if obj not in visible_objects:
                    return False

        if (self.check_pose_novelty_rot or self.check_pose_novelty_translation) and \
        (not self._check_novel_pose(cam2world_matrix)):
            return False

        if self._above_objects:
            for obj in self._above_objects:
                if self._position_is_above_object(cam2world_matrix.to_translation(), obj):
                    return True
            return False

        return True

    def _position_is_above_object(self, position, object):
        """ Make sure the given position is straight above the given object with no obstacles in between.

        :param position: The position to check.
        :param object: The query object to use.
        :return: True, if a ray sent into negative z-direction starting from the position hits the object first.
        """
        # Send a ray straight down and check if the first hit object is the query object
        hit, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(bpy.context.view_layer.depsgraph,
                                                                 position,
                                                                 mathutils.Vector([0, 0, -1]))
        return hit and hit_object == object


    def _init_bvh_tree(self):
        """ Creates a bvh tree which contains all mesh objects in the scene.

        Such a tree is later used for fast raycasting.
        """
        # Create bmesh which will contain the meshes of all objects
        bm = bmesh.new()
        # Go through all mesh objects
        for obj in get_all_blender_mesh_objects():
            if obj in self.excluded_objects_in_proximity_check:
                continue
            # Add object mesh to bmesh (the newly added vertices will be automatically selected)
            bm.from_mesh(obj.data)
            # Apply world matrix to all selected vertices
            bm.transform(obj.matrix_world, filter={"SELECT"})
            # Deselect all vertices
            for v in bm.verts:
                v.select = False

        # Create tree from bmesh
        self.bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

        self._is_bvh_tree_inited = True

    def _perform_obstacle_in_view_check(self, cam, cam2world_matrix):
        """ Check if there is an obstacle in front of the camera which is less than the configured
            "min_dist_to_obstacle" away from it.

        :param cam: The camera whose view frame is used (only FOV is relevant, pose of cam is ignored).
        :param cam2world_matrix: Transformation matrix that transforms from the camera space to the world space.
        :return: True, if there are no obstacles too close to the cam.
        """
        if not self.proximity_checks:  # if no checks are in the settings all positions are accepted
            return True
        if not self._is_bvh_tree_inited:
            raise Exception("The bvh tree should be inited before this function is called!")

        # Get position of the corners of the near plane
        frame = cam.view_frame(scene=bpy.context.scene)
        # Bring to world space
        frame = [cam2world_matrix @ v for v in frame]

        # Compute vectors along both sides of the plane
        vec_x = frame[1] - frame[0]
        vec_y = frame[3] - frame[0]

        sum = 0.0
        sum_sq = 0.0

        range_distance = sys.float_info.max

        # Input validation
        for operator in self.proximity_checks:
            if (operator == "min" or operator == "max") and not isinstance(self.proximity_checks[operator], numbers.Number):
                raise Exception("Threshold must be a number in perform_obstacle_in_view_check")
            if operator == "avg" or operator == "var":
                if "min" not in self.proximity_checks[operator] or "max" not in self.proximity_checks[operator]:
                    raise Exception("Please specify the accepted interval for the avg and var operators "
                                    "in perform_obstacle_in_view_check")
                if not isinstance(self.proximity_checks[operator]["min"], numbers.Number) \
                        or not isinstance(self.proximity_checks[operator]["max"], numbers.Number):
                    raise Exception("Threshold must be a number in perform_obstacle_in_view_check")


        # If there are no average or variance operators, we can decrease the ray range distance for efficiency
        if "avg" not in self.proximity_checks and "var" not in self.proximity_checks:
            if "max" in self.proximity_checks:
                # Cap distance values at a value slightly higher than the max threshold
                range_distance = self.proximity_checks["max"] + 1.0
            else:
                range_distance = self.proximity_checks["min"]

        no_range_distance = False
        if "no_background" in self.proximity_checks and self.proximity_checks["no_background"]:
            # when no background is on, it can not be combined with a reduced range distance
            no_range_distance = True

        # Go in discrete grid-like steps over plane
        position = cam2world_matrix.to_translation()
        for x in range(0, self.sqrt_number_of_rays):
            for y in range(0, self.sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / float(self.sqrt_number_of_rays - 1) \
                      + vec_y * y / float(self.sqrt_number_of_rays - 1)
                # Send ray from the camera position through the current point on the plane
                if no_range_distance:
                    _, _, _, dist = self.bvh_tree.ray_cast(position, end - position)
                else:
                    _, _, _, dist = self.bvh_tree.ray_cast(position, end - position, range_distance)

                # Check if something was hit and how far it is away
                if dist is not None:
                    if "min" in self.proximity_checks and dist <= self.proximity_checks["min"]:
                        return False
                    if "max" in self.proximity_checks and dist >= self.proximity_checks["max"]:
                        return False
                    if "avg" in self.proximity_checks:
                        sum += dist
                    if "var" in self.proximity_checks:
                        if not "avg" in self.proximity_checks:
                            sum += dist
                        sum_sq += dist * dist
                elif "no_background" in self.proximity_checks and self.proximity_checks["no_background"]:
                    return False

        if "avg" in self.proximity_checks:
            avg = sum / (self.sqrt_number_of_rays * self.sqrt_number_of_rays)
            # Check that the average distance is not within the accepted interval
            if avg >= self.proximity_checks["avg"]["max"] or avg <= self.proximity_checks["avg"]["min"]:
                return False

        if "var" in self.proximity_checks:
            if not "avg" in self.proximity_checks:
                avg = sum / (self.sqrt_number_of_rays * self.sqrt_number_of_rays)
            sq_avg = avg * avg

            avg_sq = sum_sq / (self.sqrt_number_of_rays * self.sqrt_number_of_rays)

            var = avg_sq - sq_avg
            # Check that the variance value of the distance is not within the accepted interval
            if var >= self.proximity_checks["var"]["max"] or var <= self.proximity_checks["var"]["min"]:
                return False

        return True

    def _visible_objects(self, cam: bpy.types.Camera, cam2world_matrix: mathutils.Matrix):
        """ Returns a set of objects visible from the given camera pose.

        Sends a grid of rays through the camera frame and returns all objects hit by at least one ray.

        :param cam: The camera whose view frame is used (only FOV is relevant, pose of cam is ignored).
        :param cam2world_matrix: The world matrix which describes the camera orientation to check.
        :return: A set of objects visible hit by the sent rays.
        """
        visible_objects = set()

        # Get position of the corners of the near plane
        frame = cam.view_frame(scene=bpy.context.scene)
        # Bring to world space
        frame = [cam2world_matrix @ v for v in frame]

        # Compute vectors along both sides of the plane
        vec_x = frame[1] - frame[0]
        vec_y = frame[3] - frame[0]

        # Go in discrete grid-like steps over plane
        position = cam2world_matrix.to_translation()
        for x in range(0, self.sqrt_number_of_rays):
            for y in range(0, self.sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / float(self.sqrt_number_of_rays - 1) + vec_y * y / float(self.sqrt_number_of_rays - 1)
                # Send ray from the camera position through the current point on the plane
                _, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(bpy.context.view_layer.depsgraph, position, end - position)
                # Add hit object to set
                visible_objects.add(hit_object)

        return visible_objects

    def _scene_coverage_score(self, cam, cam2world_matrix):
        """ Evaluate the interestingness/coverage of the scene.

        This module tries to look at as many objects at possible, this might lead to
        a focus on the same objects from similar angles.

        Only for SUNCG and 3D Front:
            Least interesting objects: walls, ceilings, floors.

        :param cam: The camera whose view frame is used (only FOV is relevant, pose of cam is ignored).
        :param cam2world_matrix: The world matrix which describes the camera orientation to check.
        :return: the scoring of the scene.
        """

        num_of_rays = self.sqrt_number_of_rays * self.sqrt_number_of_rays
        score = 0.0
        objects_hit = defaultdict(int)

        # Get position of the corners of the near plane
        frame = cam.view_frame(scene=bpy.context.scene)
        # Bring to world space
        frame = [cam2world_matrix @ v for v in frame]

        # Compute vectors along both sides of the plane
        vec_x = frame[1] - frame[0]
        vec_y = frame[3] - frame[0]

        # Go in discrete grid-like steps over plane
        position = cam2world_matrix.to_translation()
        for x in range(0, self.sqrt_number_of_rays):
            for y in range(0, self.sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / float(self.sqrt_number_of_rays - 1) + vec_y * y / float(self.sqrt_number_of_rays - 1)
                # Send ray from the camera position through the current point on the plane
                hit, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(bpy.context.view_layer.depsgraph, position, end - position)

                if hit:
                    is_of_special_dataset = "is_suncg" in hit_object or "is_3d_front" in hit_object
                    if is_of_special_dataset and "type" in hit_object and hit_object["type"] == "Object":
                        # calculate the score based on the type of the object,
                        # wall, floor and ceiling objects have 0 score
                        if "coarse_grained_class" in hit_object:
                            object_class = hit_object["coarse_grained_class"]
                            objects_hit[object_class] += 1
                            if object_class in self.special_objects:
                                score += self.special_objects_weight
                            else:
                                score += 1
                        else:
                            score += 1
                    elif "category_id" in hit_object:
                        object_class = hit_object["category_id"]
                        if object_class in self.special_objects:
                            score += self.special_objects_weight
                        else:
                            score += 1
                        objects_hit[object_class] += 1
                    else:
                        objects_hit[hit_object] += 1
                        score += 1
        # For a scene with three different objects, the starting variance is 1.0, increases/decreases by '1/3' for
        # each object more/less, excluding floor, ceiling and walls
        scene_variance = len(objects_hit) / 3.0
        for object_hit_value in objects_hit.values():
            # For an object taking half of the scene, the scene_variance is halved, this penalizes non-even
            # distribution of the objects in the scene
            scene_variance *= 1.0 - object_hit_value / float(num_of_rays)
        score = scene_variance * (score / float(num_of_rays))
        return score

    def _check_novel_pose(self, cam2world_matrix):
        """ Checks if a newly sampled pose is novel based on variance checks.

        :param cam2world_matrix: camera pose to check
        """

        def _variance_constraint(array, new_val, old_var, diff_threshold, mode):
            array.append(new_val)
            var = np.var(array)

            if var < old_var:
                array.pop()
                return False

            diff = ((var - old_var) / old_var) * 100.0
            print("Variance difference {}: {}".format(mode, diff))
            if diff < diff_threshold:  # Check if the variance increased sufficiently
                array.pop()
                return False

            return True

        translation = cam2world_matrix.to_translation()
        rotation    = cam2world_matrix.to_euler()

        if len(self.translations) != 0 and len(self.rotations) != 0:  # First pose is always novel

            if self.check_pose_novelty_rot:
                if not _variance_constraint(self.rotations, rotation, self.var_rot, self.min_var_diff_rot, "rotation"):
                    return False

            if self.check_pose_novelty_translation:
                if not _variance_constraint(self.translations, translation, self.var_translation,
                                            self.min_var_diff_translation, "translation"):
                    return False
        else:
            self.translations.append(translation)
            self.rotations.append(rotation)

        self.var_rot = np.var(self.rotations)
        self.var_translation = np.var(self.translations)

        return True 
