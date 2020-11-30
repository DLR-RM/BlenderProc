import random

import bpy

from src.camera.CameraSampler import CameraSampler
from src.utility.CameraUtility import CameraUtility
from src.utility.Config import Config


class SuncgCameraSampler(CameraSampler):
    """ Samples valid camera poses inside suncg rooms.

    Works as the standard camera sampler, except the following differences:
    - Always sets the x and y coordinate of the camera location to a value uniformly sampled inside a rooms bounding box
    - The configured z coordinate of the configured camera location is used as relative to the floor
    - All sampled camera locations need to lie straight above the room's floor to be valid
    
    See parent class CameraSampler for more details.

    """
    def __init__(self, config):
        CameraSampler.__init__(self, config)

    def run(self):
        # Collect all valid room objects
        self.rooms = []
        for room_obj in bpy.context.scene.objects:
            # Check if object is from type room and has bbox
            if "type" in room_obj and room_obj["type"] == "Room" and "bbox" in room_obj:

                # Make sure the room has a floor which is required for sampling
                floor_obj = self._find_floor(room_obj)
                if floor_obj is not None:
                    self.rooms.append((room_obj, floor_obj))

        super().run()

    def sample_and_validate_cam_pose(self, cam, cam_ob, config):
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: The config object describing how to sample
        :return: True, if the sampled pose was valid
        """
        # Sample room
        room_id = random.randrange(len(self.rooms))
        room_obj, floor_obj = self.rooms[room_id]

        # Sample/set intrinsics
        self._set_cam_intrinsics(cam, Config(self.config.get_raw_dict("intrinsics", {})))

        # Sample camera extrinsics (we do not set them yet for performance reasons)
        cam2world_matrix = self._cam2world_matrix_from_cam_extrinsics(config)

        # Make sure the sampled location is inside the room => overwrite x and y and add offset to z
        cam2world_matrix.translation[0] = random.uniform(room_obj["bbox"]["min"][0], room_obj["bbox"]["max"][0])
        cam2world_matrix.translation[1] = random.uniform(room_obj["bbox"]["min"][1], room_obj["bbox"]["max"][1])
        cam2world_matrix.translation[2] += room_obj["bbox"]["min"][2]

        # Check if sampled pose is valid
        if self._is_pose_valid(floor_obj, cam, cam_ob, cam2world_matrix):
            # Set camera extrinsics as the pose is valid
            frame = CameraUtility.add_camera_pose(cam2world_matrix)
            cam_ob["room_id"] = room_id
            # As the room id depends on the camera pose and therefore on the keyframe, we also need to add keyframes for the room id
            cam_ob.keyframe_insert(data_path='["room_id"]', frame=frame)
            return True
        else:
            return False

    def _is_pose_valid(self, floor_obj, cam, cam_ob, cam2world_matrix):
        """ Determines if the given pose is valid.

        - Checks if the pose is above the floor
        - Checks if the distance to objects is in the configured range
        - Checks if the scene coverage score is above the configured threshold

        :param floor_obj: The floor object of the room the camera was sampled in.
        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param cam2world_matrix: The sampled camera extrinsics in form of a camera to world frame transformation matrix.
        :return: True, if the pose is valid
        """
        if not self._position_is_above_object(cam2world_matrix.to_translation(), floor_obj):
            return False

        return super()._is_pose_valid(cam, cam_ob, cam2world_matrix)

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
