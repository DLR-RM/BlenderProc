import ast
import os
import random

import bpy

from src.camera.CameraSampler import CameraSampler
from src.utility.CameraUtility import CameraUtility
from src.utility.Utility import Utility


class ReplicaCameraSampler(CameraSampler):
    """ Samples valid camera poses inside replica rooms.

        Works as the standard camera sampler, except the following differences:
        - Always sets the x and y coordinate of the camera location to a value uniformly sampled inside of a room's
          bounding box
        - The configured z coordinate of the configured camera location is used as relative to the floor
        - All sampled camera locations need to lie straight above the room's floor to be valid
        - Using the scene coverage/interestingness score in the ReplicaCameraSampler does not make much sense, as the
          3D mesh is not split into individual objects.

        See parent class CameraSampler for more details.

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "is_replica_object", "Whether it's a Replica object. Type: bool. Default: False."
        "height_list_path", "Path to height list. Type: string."
        "data_set_name", "Dataset name in case is_replica_object is set to false. Type: string."
    """

    def __init__(self, config):
        CameraSampler.__init__(self, config)

    def run(self):
        """ Samples multiple cameras per suncg room.

        Procedure per room:
         - sample position (x,y) inside bounding box of the whole scene, the z component is fixed by the camera_height
         - send ray from position straight down and make sure it hits the floor object of the scene
         - send rays through the field of view to approximate a depth map and to make sure no obstacle is too close to the camera
        """
        # Determine bounding box of the scene
        if 'mesh' in bpy.data.objects:
            bounding_box = bpy.data.objects['mesh'].bound_box
            self.bounding_box = {"min": bounding_box[0], "max": bounding_box[-2]}
        else:
            raise Exception("Mesh object is not defined!")

        # Find floor object
        if 'floor' in bpy.data.objects:
            self.floor_object = bpy.data.objects['floor']
        else:
            raise Exception("No floor object is defined!")

        # Load the height levels of this scene
        if not self.config.get_bool('is_replica_object', False):
            file_path = self.config.get_string('height_list_path')
        else:
            folder_path = os.path.join('resources', 'replica_dataset', 'height_levels', self.config.get_string('data_set_name'))
            file_path = Utility.resolve_path(os.path.join(folder_path, 'height_list_values.txt'))
        with open(file_path) as file:
            self.floor_height_values = [float(val) for val in ast.literal_eval(file.read())]

        super().run()

    def sample_and_validate_cam_pose(self, cam, cam_ob, config):
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: The config object describing how to sample
        :return: True, if the sampled pose was valid
        """
        # Sample/set intrinsics
        self._set_cam_intrinsics(cam, config)

        # Sample camera extrinsics (we do not set them yet for performance reasons)
        cam2world_matrix = self._cam2world_matrix_from_cam_extrinsics(config)

        # Make sure the sampled location is inside the room => overwrite x and y and add offset to z
        cam2world_matrix.translation[0] = random.uniform(self.bounding_box["min"][0], self.bounding_box["max"][0])
        cam2world_matrix.translation[1] = random.uniform(self.bounding_box["min"][1], self.bounding_box["max"][1])
        cam2world_matrix.translation[2] += self.floor_height_values[random.randrange(0, len(self.floor_height_values))]

        # Check if sampled pose is valid
        if self._is_pose_valid(cam, cam_ob, cam2world_matrix):
            # Set camera extrinsics as the pose is valid
            CameraUtility.add_camera_pose(cam2world_matrix)
            return True
        else:
            return False

    def _is_pose_valid(self, cam, cam_ob, cam2world_matrix):
        """ Determines if the given pose is valid.

        - Checks if the pose is above the floor
        - Checks if the distance to objects is in the configured range
        - Checks if the scene coverage score is above the configured threshold

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param cam2world_matrix: The sampled camera extrinsics in form of a camera to world frame transformation matrix.
        :return: True, if the pose is valid
        """
        if not self._position_is_above_object(cam2world_matrix.to_translation(), self.floor_object):
            return False

        return super()._is_pose_valid(cam, cam_ob, cam2world_matrix)

