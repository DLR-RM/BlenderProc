import math
from collections import defaultdict

import bpy
import mathutils

from src.camera.CameraSampler import CameraSampler
from src.utility.BoundingBoxSampler import BoundingBoxSampler

class SuncgCameraSampler(CameraSampler):
    """ Samples multiple cameras per suncg room.

    Procedure per room:
     - sample position inside bbox
     - send ray from position straight down and make sure it hits the room's floor first
     - send rays through the field of view to approximate a depth map and to make sure no obstacle is too close to the camera

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "position_range_x, position_range_y, position_range_z", "The interval in which the camera positions should be sampled. The interval is specified as a list of two values (min and max value). The values are used relative to the bbox, so e.q. a z-interval of [1, 2] means between 1 and 2 meter above the floor."
       "cams_per_square_meter", "Used to calculate the number of cams that should be sampled in a given room. total_cams = cams_per_square_meter * room_size"
       "max_tries_per_room", "The maximum number of tries that should be made to sample the requested number of cam poses for a given room."
       "resolution_x", "The resolution of the camera in x-direction. Necessary when checking, if there are obstacles in front of the camera."
       "resolution_y", "The resolution of the camera in y-direction.Necessary when checking, if there are obstacles in front of the camera."
       "pixel_aspect_x", "The aspect ratio of the camera's viewport. Necessary when checking, if there are obstacles in front of the camera."
       "min_interest_score", "Arbitrary threshold to discard cam poses with less interesting views."
       "special_objects", "Objects that weights differently in calculating whether the scene is interesting or not, uses the coarse_grained_class."
       "special_objects_weight", "Weighting factor for more special objects, used to estimate the interestingness of the scene."
    """
    def __init__(self, config):
        CameraSampler.__init__(self, config)
        self.cams_per_square_meter = self.config.get_float("cams_per_square_meter", 0.5)
        self.max_tries_per_room = self.config.get_int("max_tries_per_room", 10000)
        self.min_interest_score = self.config.get_float("min_interest_score", 0.3)
        self.special_objects = self.config.get_list("special_objects", [])
        self.special_objects_weight = self.config.get_float("special_objects_weight", 2)

        self.position_ranges = [
            self.config.get_list("position_range_x", []),
            self.config.get_list("position_range_y", []),
            self.config.get_list("position_range_z", [1.4, 1.4])
        ]

    def run(self):
        self._init_bvh_tree()

        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        # Set resolution and aspect ratio, as they have an influence on the near plane
        bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", 512)
        bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", 512)
        bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1)

        room_id = 0
        for room_obj in bpy.context.scene.objects:
            # Find room objects
            if "type" in room_obj and room_obj["type"] == "Room" and "bbox" in room_obj:

                floor_obj = self._find_floor(room_obj)
                if floor_obj is None:
                    continue

                number_of_cams = self._calc_number_of_cams_in_room(room_obj)
                print("Generating " + str(number_of_cams) + " cams for room " + room_obj.name + " (" + str(room_obj["roomTypes"]) + ")")

                # Now try to generate the requested number of cams
                successful_tries = 0
                tries = 0
                while successful_tries < number_of_cams and tries < self.max_tries_per_room:

                    tries += 1
                    position = self._sample_position(room_obj)

                    if not self._position_is_above_floor(position, floor_obj):
                        continue

                    orientation = self._sample_orientation()

                    # Compute the world matrix of a cam with the given pose
                    world_matrix = mathutils.Matrix.Translation(mathutils.Vector(position)) @ mathutils.Euler(orientation, 'XYZ').to_matrix().to_4x4()

                    if not self._perform_obstacle_in_view_check(cam, position, world_matrix):
                        continue

                    if self._scene_coverage_score(cam, position, world_matrix) < self.min_interest_score:
                        continue

                    # Set the camera pose at the next frame
                    self.cam_pose_collection.add_item({
                        "location": position,
                        "rotation": orientation
                    })

                    successful_tries += 1

                print(str(tries) + " tries were necessary")
                room_id += 1

        self._register_cam_pose_output()


    def _sample_position(self, room_obj):
        """ Samples a random position inside the bbox of the given room object.

        :param room_obj: The room object whose bbox is used.
        :return: A vector describing the sampled position
        """

        max = mathutils.Vector()
        min = mathutils.Vector()
        for i in range(3):
            # Check if an interval for sampling has been configured, otherwise sample inside bbox
            if len(self.position_ranges[i]) != 2:
                min[i] = room_obj["bbox"]["min"][i]
                max[i] = room_obj["bbox"]["max"][i]
            else:
                min[i] = room_obj["bbox"]["min"][i] + self.position_ranges[i][0]
                max[i] = room_obj["bbox"]["min"][i] + self.position_ranges[i][1]

        return BoundingBoxSampler.sample(min, max)


    def _calc_number_of_cams_in_room(self, room_obj):
        """ Approximates the square meters of the room and then uses cams_per_square_meter to get total number of cams in room.

        :param room_obj: The room object whose bbox will be used to approximate the size.
        :return: The number of camera positions planned for this room.
        """
        return math.floor(abs(room_obj["bbox"]["max"][0] - room_obj["bbox"]["min"][0]) * abs(room_obj["bbox"]["max"][1] - room_obj["bbox"]["min"][1]) * self.cams_per_square_meter)

    def _find_floor(self, room_obj):
        """ Returns the floor object of the given room object.

        Goes through all children and returns the first one with type "Floor".

        :param room_obj: The room object.
        :return: The found floor object or None if none has been found.
        """
        for obj in bpy.context.scene.objects:
            if obj.parent == room_obj and "type" in obj and obj["type"] == "Floor":
                return obj
        return None

    def _position_is_above_floor(self, position, floor_obj):
        """ Make sure the given position is straight above the given floor object with no obstacles in between.

        :param position: The position to check.
        :param floor_obj: The floor object to use.
        :return: True, if a ray sent into negative z-direction starting from the position hits the floor first.
        """

        return self._position_is_above_object(position, floor_obj)

    def _scene_coverage_score(self, cam, position, world_matrix):
        """ Evaluate the interestingness/coverage of the scene.

        Least interesting objects: walls, ceilings, floors.

        :param cam: The camera whose view frame is used (only FOV is relevant, pose of cam is ignored).
        :param position: The camera position vector to check
        :param world_matrix: The world matrix which describes the camera orientation to check.
        :return: the scoring of the scene.
        """

        num_of_rays = self.sqrt_number_of_rays * self.sqrt_number_of_rays
        score = 0.0
        scene_variance = 0.0
        objects_hit = defaultdict(int)

        # Get position of the corners of the near plane
        frame = cam.view_frame(scene=bpy.context.scene)
        # Bring to world space
        frame = [world_matrix @ v for v in frame]

        # Compute vectors along both sides of the plane
        vec_x = frame[1] - frame[0]
        vec_y = frame[3] - frame[0]

        # Go in discrete grid-like steps over plane
        for x in range(0, self.sqrt_number_of_rays):
            for y in range(0, self.sqrt_number_of_rays):
                # Compute current point on plane
                end = frame[0] + vec_x * x / float(self.sqrt_number_of_rays - 1) + vec_y * y / float(self.sqrt_number_of_rays - 1)
                # Send ray from the camera position through the current point on the plane

                hit, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(bpy.context.view_layer, position, end - position)

                # calculate the score based on the type of the object, wall, floor and ceiling objects have 0 score
                if hit and "type" in hit_object and hit_object["type"] == "Object":
                    if "coarse_grained_class" in hit_object:
                        object_class = hit_object["coarse_grained_class"]
                        objects_hit[object_class] += 1
                        if object_class in self.special_objects:
                            score += self.special_objects_weight
                        else:
                            score += 1
                    else:
                        score += 1


        # For a scene with three different objects, the starting variance is 1.0, increases/decreases by '1/3' for each object more/less, excluding floor, ceiling and walls
        scene_variance = len(objects_hit.keys()) / 3
        for object_hit in objects_hit.keys():
            # For an object taking half of the scene, the scene_variance is halved, this pentalizes non-even distribution of the objects in the scene
            scene_variance *= 1 - objects_hit[object_hit] / num_of_rays

        score = scene_variance * (score / num_of_rays)
        return score
