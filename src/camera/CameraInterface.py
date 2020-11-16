import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler

from src.main.Module import Module
from src.utility.CameraUtility import CameraUtility
from src.utility.Utility import Utility
from src.utility.MathUtility import MathUtility


class CameraInterface(Module):
    """ A super class for camera related modules. Holding key information like camera intrinsics and extrinsics,
        in addition to setting stereo parameters.

        Example 1: Setting a custom source frame while specifying the format of the rotation. Note that to set config
                   parameters here, it has to be in a child class of CameraInterface.

        {
          "module": "camera.CameraLoader",
          "config": {
            "path": "<args:0>",
            "file_format": "location rotation/value _ _ _ _ _ _",
            "source_frame": ["X", "-Z", "Y"],
            "default_cam_param": {
              "rotation": {
                "format": "forward_vec"
              }
            },
            "intrinsics: {
              "fov": 1
            }
          }
        }

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "source_frame", "Can be used if the given positions and rotations are specified in frames different from the "
                        "blender frame. Has to be a list of three strings. Example: ['X', '-Z', 'Y']: Point (1,2,3) "
                        "will be transformed to (1, -3, 2). Type: list. Default: ["X", "Y", "Z"]. "
                        "Available: ['X', 'Y', 'Z', '-X', '-Y', '-Z']."
        "cam_poses", "A list of dicts, where each dict specifies one cam pose. See the next table for details about specific properties. Type: list."
        "default_cam_param", "Properties across all cam poses. Type: dict."

    **Properties per cam pose**:

    .. csv-table::
        :header: "Keyword", "Description"

        "location", "The position of the camera, specified as a list of three values (xyz). Type: mathutils.Vector."
        "rotation/value", "Specifies the rotation of the camera. Per default rotations are specified as three euler "
                          "angles. Type: mathutils.Vector."
        "rotation/format", "Describes the form in which the rotation is specified. Type: string. Available: 'euler' "
                           "(three Euler angles), 'forward_vec'(specified with a forward vector: the Y-Axis is assumed "
                           "as Up-Vector), 'look_at' (camera will be turned such as it looks at 'value' location, which "
                           "can be defined as a fixed or sampled XYZ location)."
        "rotation/inplane_rot", "A rotation angle in radians around the Z axis. Type: float. Default: 0.0"
        "cam2world_matrix", "4x4 camera extrinsic matrix. Type: list of floats. Default: []."


    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.source_frame = self.config.get_list("source_frame", ["X", "Y", "Z"])

    def _set_cam_extrinsics(self, cam_ob, config):
        """ Sets camera extrinsics according to the config.

        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: A configuration object with cam extrinsics.
        """
        cam2world_matrix = self._cam2world_matrix_from_cam_extrinsics(config)
        CameraUtility.add_camera_pose(cam2world_matrix)

    def _cam2world_matrix_from_cam_extrinsics(self, config):
        """ Determines camera extrinsics by using the given config and returns them in form of a cam to world frame transformation matrix.

        :param config: The configuration object.
        :return: The cam to world transformation matrix.
        """
        if not config.has_param("cam2world_matrix"):
            position = MathUtility.transform_point_to_blender_coord_frame(config.get_vector3d("location", [0, 0, 0]), self.source_frame)

            # Rotation
            rotation_format = config.get_string("rotation/format", "euler")
            value = config.get_vector3d("rotation/value", [0, 0, 0])
            # Transform to blender coord frame
            value = MathUtility.transform_point_to_blender_coord_frame(Vector(value), self.source_frame)
            if rotation_format == "euler":
                # Rotation, specified as euler angles
                rotation_matrix = Euler(value, 'XYZ').to_matrix()
            elif rotation_format == "forward_vec":
                # Convert forward vector to euler angle (Assume Up = Z)
                rotation_matrix = CameraUtility.rotation_from_forward_vec(value)
            elif rotation_format == "look_at":
                # Convert forward vector to euler angle (Assume Up = Z)
                rotation_matrix = CameraUtility.rotation_from_forward_vec((value - position).normalized())
            else:
                raise Exception("No such rotation format:" + str(rotation_format))

            if rotation_format == "look_at" or rotation_format == "forward_vec":
                inplane_rot = config.get_float("rotation/inplane_rot", 0.0)
                rotation_matrix = rotation_matrix @ Euler((0.0, 0.0, inplane_rot)).to_matrix()

            cam2world_matrix = Matrix.Translation(Vector(position)) @ rotation_matrix.to_4x4()
        else:
            cam2world_matrix = Matrix(np.array(config.get_list("cam2world_matrix")).reshape(4, 4).astype(np.float32))

        return cam2world_matrix
