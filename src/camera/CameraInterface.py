import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler

from src.main.Module import Module
from src.utility.Utility import Utility


class CameraInterface(Module):
    """ A super class for camera related modules. Holding key information like camera intrinsics and extrinsics,
        in addition to setting stereo parameters.

        Example 1: Setting a custom source frame while specifying the format of the rotation. Note that to set config
                   parameters here, it has to be in a child class of CameraInterface.

        {
          "module": "camera.CameraLoader",
          "config": {
            "path": "<args:0>",
            "file_format": "location rotation/value _ _ _ fov _ _",
            "source_frame": ["X", "-Z", "Y"],
            "default_cam_param": {
              "rotation": {
                "format": "forward_vec"
              },
            "fov_is_half": true
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
        "default_cam_param", "Properties across all cam poses. See the next table for details. Type: dict."

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
        "shift", "Principal Point deviation from center. The unit is proportion of the larger image dimension. Type: float."
        "fov", "The FOV (normally the angle between both sides of the frustum, if fov_is_half is True than its assumed "
               "to be the angle between forward vector and one side of the frustum). Type: float. Default: 0.691111."
        "cam_K", "Camera Matrix K. Type: list. Default: []."
        "resolution_x", "Width resolution of the camera. Type: int. Default: 512. "
        "resolution_y", "Height resolution of the camera. Type: int. Default: 512. "
        "cam2world_matrix", "4x4 camera extrinsic matrix. Type: list of floats. Default: []."
        "fov_is_half", "Set to true if the given FOV specifies the angle between forward vector and one side of the "
                       "frustum. Type: bool. Default: False."
        "pixel_aspect_x", "Pixel aspect ratio. Type: float. Default: 1."
        "clip_start", "Near clipping. Type: float. Default: 0.1."
        "clip_end", "Far clipping. Type: float. Default: 1000."
        "stereo_convergence_mode", "How the two cameras converge (e.g. Off-Axis where both cameras are shifted inwards "
                                   "to converge in the convergence plane, or parallel where they do not converge and "
                                   "are parallel). Type: string. Default: "OFFAXIS"."
        "convergence_distance", "The convergence point for the stereo cameras (i.e. distance from the projector to the "
                                "projection screen). Type: float. Default: 1.95."
        "interocular_distance", "Distance between the camera pair. Type: float. Default: 0.065."
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.source_frame = self.config.get_list("source_frame", ["X", "Y", "Z"])

    def _insert_key_frames(self, cam, cam_ob, frame_id):
        """ Insert key frames for all relevant camera attributes.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param frame_id: The frame number where key frames should be inserted.
        """
        cam.keyframe_insert(data_path='clip_start', frame=frame_id)
        cam.keyframe_insert(data_path='clip_end', frame=frame_id)

        cam.keyframe_insert(data_path='shift_x', frame=frame_id)
        cam.keyframe_insert(data_path='shift_y', frame=frame_id)

        cam_ob.keyframe_insert(data_path='location', frame=frame_id)
        cam_ob.keyframe_insert(data_path='rotation_euler', frame=frame_id)

    def _set_cam_intrinsics(self, cam, config):
        """ Sets camera intrinsics from a source with following priority

           1. from config function parameter if defined
           2. from module config (self.config) if defined
           3. custom property cam['loaded_intrinsics'] if set in Loader
           4. default config
                resolution_x/y: 512 
                pixel_aspect_x: 1
                clip_start:   : 0.1
                clip_end      : 1000
                fov           : 0.691111
        :param config: A configuration object with cam intrinsics.
        """
        width, height = self.config.get_int("resolution_x", 512), self.config.get_int("resolution_y", 512)
        if 'loaded_resolution' in cam and not self.config.has_param('resolution_x'):
            width, height = cam['loaded_resolution']
        bpy.context.scene.render.resolution_x = width
        bpy.context.scene.render.resolution_y = height
        
        # If defined, get cam_K from config else from self.config
        cam_K = config.get_list("cam_K", self.config.get_list("cam_K", []))
        if cam_K:
            cam['loaded_intrinsics'] = cam_K        

        # Convert intrinsics from loader/config to Blender format
        cam.lens_unit = 'FOV'
        if 'loaded_intrinsics' in cam:
            if self.config.has_param("fov"):
                print('WARNING: FOV defined in config is ignored. Mutually exclusive with cam_K')
            if self.config.has_param("pixel_aspect_x"):
                print('WARNING: pixel_aspect_x defined in config is ignored. Mutually exclusive with cam_K')
            
            cam_K = np.array(cam['loaded_intrinsics']).reshape(3, 3).astype(np.float32)
            
            # Convert focal lengths to FOV
            cam.angle = 2 * np.arctan(width / (2 * cam_K[0, 0]))
            
            fx, fy = cam_K[0,0], cam_K[1,1]
            cx, cy = cam_K[0,2], cam_K[1,2]

            # If fx!=fy change pixel aspect ratio
            if fx > fy:
                bpy.context.scene.render.pixel_aspect_y = fx/fy
            elif fx < fy:
                bpy.context.scene.render.pixel_aspect_x = fy/fx

            # Convert principal point cx,cy in px to blender cam shift in proportion to larger image dim 
            max_resolution = max(width, height)
            cam.shift_x = -(cx - width / 2.0) / max_resolution
            cam.shift_y = (cy - height / 2.0) / max_resolution
        else:
            # Set FOV (Default value is the same as the default blender value)
            cam.angle = config.get_float(self.config.get_float("fov", 0.691111))

            # Set Pixel Aspect Ratio
            bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1)
            
            if bpy.context.scene.render.pixel_aspect_x != 1:
                print('WARNING: Using non-square pixel aspect ratio. Can influence intrinsics.')

            # FOV is sometimes also given as the angle between forward vector and one side of the frustum
            if self.config.get_bool("fov_is_half", False):
                cam.angle *= 2

        # Clipping (Default values are the same as default blender values)
        cam.clip_start = config.get_float(self.config.get_float("clip_start", 0.1))
        cam.clip_end = config.get_float(self.config.get_float("clip_end", 1000))

        # How the two cameras converge (e.g. Off-Axis where both cameras are shifted inwards to converge in the
        # convergence plane, or parallel where they do not converge and are parallel)
        cam.stereo.convergence_mode = self.config.get_string("stereo_convergence_mode", "OFFAXIS")
        # The convergence point for the stereo cameras (i.e. distance from the projector to the projection screen) (Default value is the same as the default blender value)
        cam.stereo.convergence_distance = self.config.get_float("convergence_distance", 1.95)
        # Distance between the camera pair (Default value is the same as the default blender value)
        cam.stereo.interocular_distance = self.config.get_float("interocular_distance", 0.065)


    def _set_cam_extrinsics(self, cam_ob, config):
        """ Sets camera extrinsics according to the config.

        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: A configuration object with cam extrinsics.
        """
        cam2world_matrix = self._cam2world_matrix_from_cam_extrinsics(config)
        cam_ob.matrix_world = cam2world_matrix

    def _cam2world_matrix_from_cam_extrinsics(self, config):
        """ Determines camera extrinsics by using the given config and returns them in form of a cam to world frame transformation matrix.

        :param config: The configuration object.
        :return: The cam to world transformation matrix.
        """
        if not config.has_param("cam2world_matrix"):
            position = Utility.transform_point_to_blender_coord_frame(config.get_vector3d("location", [0, 0, 0]), self.source_frame)

            # Rotation
            rotation_format = config.get_string("rotation/format", "euler")
            value = config.get_vector3d("rotation/value", [0, 0, 0])
            if rotation_format == "euler":
                # Rotation, specified as euler angles
                rotation_euler = Utility.transform_point_to_blender_coord_frame(value, self.source_frame)
            elif rotation_format == "forward_vec":
                # Rotation, specified as forward vector
                forward_vec = Vector(Utility.transform_point_to_blender_coord_frame(value, self.source_frame))
                # Convert forward vector to euler angle (Assume Up = Z)
                rotation_euler = forward_vec.to_track_quat('-Z', 'Y').to_euler()
            elif rotation_format == "look_at":
                # Compute forward vector
                forward_vec = value - position
                forward_vec.normalize()
                # Convert forward vector to euler angle (Assume Up = Z)
                rotation_euler = forward_vec.to_track_quat('-Z', 'Y').to_euler()
            else:
                raise Exception("No such rotation format:" + str(rotation_format))

            rotation_matrix = Euler(rotation_euler, 'XYZ').to_matrix()

            if rotation_format == "look_at" or rotation_format == "forward_vec":
                inplane_rot = config.get_float("rotation/inplane_rot", 0.0)
                rotation_matrix = rotation_matrix @ Euler((0.0, 0.0, inplane_rot)).to_matrix()

            cam2world_matrix = Matrix.Translation(Vector(position)) @ rotation_matrix.to_4x4()
        else:
            cam2world_matrix = Matrix(np.array(config.get_list("cam2world_matrix")).reshape(4, 4).astype(np.float32))
        return cam2world_matrix
