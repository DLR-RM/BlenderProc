import numbers
from collections import defaultdict

import bpy
import sys
import numpy as np
import mathutils


class CameraValidation:

    @staticmethod
    def perform_obstacle_in_view_check(cam, cam2world_matrix, proximity_checks, bvh_tree, sqrt_number_of_rays):
        """ Check if there is an obstacle in front of the camera which is less than the configured
            "min_dist_to_obstacle" away from it.

        :param cam: The camera whose view frame is used (only FOV is relevant, pose of cam is ignored).
        :param cam2world_matrix: Transformation matrix that transforms from the camera space to the world space.
        :return: True, if there are no obstacles too close to the cam.
        """
        if not proximity_checks:  # if no checks are in the settings all positions are accepted
            return True

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
        for operator in proximity_checks:
            if (operator == "min" or operator == "max") and not isinstance(proximity_checks[operator], numbers.Number):
                raise Exception("Threshold must be a number in perform_obstacle_in_view_check")
            if operator == "avg" or operator == "var":
                if "min" not in proximity_checks[operator] or "max" not in proximity_checks[operator]:
                    raise Exception("Please specify the accepted interval for the avg and var operators "
                                    "in perform_obstacle_in_view_check")
                if not isinstance(proximity_checks[operator]["min"], numbers.Number) or not isinstance(proximity_checks[operator]["max"], numbers.Number):
                    raise Exception("Threshold must be a number in perform_obstacle_in_view_check")

        # If there are no average or variance operators, we can decrease the ray range distance for efficiency
        if "avg" not in proximity_checks and "var" not in proximity_checks:
            if "max" in proximity_checks:
                # Cap distance values at a value slightly higher than the max threshold
                range_distance = proximity_checks["max"] + 1.0
            else:
                range_distance = proximity_checks["min"]

        no_range_distance = False
        if "no_background" in proximity_checks and proximity_checks["no_background"]:
            # when no background is on, it can not be combined with a reduced range distance
            no_range_distance = True

        # Go in discrete grid-like steps over plane
        position = cam2world_matrix.to_translation()
        for x in range(0, sqrt_number_of_rays):
            for y in range(0, sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / float(sqrt_number_of_rays - 1) + vec_y * y / float(sqrt_number_of_rays - 1)
                # Send ray from the camera position through the current point on the plane
                if no_range_distance:
                    _, _, _, dist = bvh_tree.ray_cast(position, end - position)
                else:
                    _, _, _, dist = bvh_tree.ray_cast(position, end - position, range_distance)

                # Check if something was hit and how far it is away
                if dist is not None:
                    if "min" in proximity_checks and dist <= proximity_checks["min"]:
                        return False
                    if "max" in proximity_checks and dist >= proximity_checks["max"]:
                        return False
                    if "avg" in proximity_checks:
                        sum += dist
                    if "var" in proximity_checks:
                        if not "avg" in proximity_checks:
                            sum += dist
                        sum_sq += dist * dist
                elif "no_background" in proximity_checks and proximity_checks["no_background"]:
                    return False

        if "avg" in proximity_checks:
            avg = sum / (sqrt_number_of_rays * sqrt_number_of_rays)
            # Check that the average distance is not within the accepted interval
            if avg >= proximity_checks["avg"]["max"] or avg <= proximity_checks["avg"]["min"]:
                return False

        if "var" in proximity_checks:
            if not "avg" in proximity_checks:
                avg = sum / (sqrt_number_of_rays * sqrt_number_of_rays)
            sq_avg = avg * avg

            avg_sq = sum_sq / (sqrt_number_of_rays * sqrt_number_of_rays)

            var = avg_sq - sq_avg
            # Check that the variance value of the distance is not within the accepted interval
            if var >= proximity_checks["var"]["max"] or var <= proximity_checks["var"]["min"]:
                return False

        return True

    @staticmethod
    def visible_objects(cam: bpy.types.Camera, cam2world_matrix: mathutils.Matrix, sqrt_number_of_rays):
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
        for x in range(0, sqrt_number_of_rays):
            for y in range(0, sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / float(sqrt_number_of_rays - 1) + vec_y * y / float(sqrt_number_of_rays - 1)
                # Send ray from the camera position through the current point on the plane
                _, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(bpy.context.view_layer.depsgraph, position, end - position)
                # Add hit object to set
                visible_objects.add(hit_object)

        return visible_objects

    @staticmethod
    def scene_coverage_score(cam, cam2world_matrix, special_objects, special_objects_weight, sqrt_number_of_rays):
        """ Evaluate the interestingness/coverage of the scene.

        This module tries to look at as many objects at possible, this might lead to
        a focus on the same objects from similar angles.

        Only for SUNCG and 3D Front:
            Least interesting objects: walls, ceilings, floors.

        :param cam: The camera whose view frame is used (only FOV is relevant, pose of cam is ignored).
        :param cam2world_matrix: The world matrix which describes the camera orientation to check.
        :return: the scoring of the scene.
        """

        num_of_rays = sqrt_number_of_rays * sqrt_number_of_rays
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
        for x in range(0, sqrt_number_of_rays):
            for y in range(0, sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / float(sqrt_number_of_rays - 1) + vec_y * y / float(sqrt_number_of_rays - 1)
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
                            if object_class in special_objects:
                                score += special_objects_weight
                            else:
                                score += 1
                        else:
                            score += 1
                    elif "category_id" in hit_object:
                        object_class = hit_object["category_id"]
                        if object_class in special_objects:
                            score += special_objects_weight
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

    @staticmethod
    def decrease_interest_score(interest_score, min_interest_score, interest_score_step):
        if interest_score <= min_interest_score:
            return False, interest_score
        else:
            return True, interest_score - interest_score_step

    @staticmethod
    def check_novel_pose(cam2world_matrix, existing_poses, check_pose_novelty_rot, check_pose_novelty_translation, min_var_diff_rot, min_var_diff_translation):
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

        if len(existing_poses) > 0:  # First pose is always novel
            if check_pose_novelty_rot:
                rotations = [pose.to_euler() for pose in existing_poses]
                var_rot = np.var(rotations)

                if not _variance_constraint(rotations, cam2world_matrix.to_euler(), var_rot, min_var_diff_rot, "rotation"):
                    return False

            if check_pose_novelty_translation:
                translations = [pose.to_translation() for pose in existing_poses]
                var_translation = np.var(translations)

                if not _variance_constraint(translations, cam2world_matrix.to_translation(), var_translation, min_var_diff_translation, "translation"):
                    return False

        return True

    @staticmethod
    def position_is_above_object(position, object):
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
