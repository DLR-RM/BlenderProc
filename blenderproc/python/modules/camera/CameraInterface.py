import bpy
import numpy as np
from mathutils import Euler

import blenderproc.python.camera.CameraUtility as CameraUtility
from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.utility.MathUtility import change_coordinate_frame_of_point, change_source_coordinate_frame_of_transformation_matrix, change_target_coordinate_frame_of_transformation_matrix, build_transformation_mat


class CameraInterface(Module):
    """
    A super class for camera related modules. Holding key information like camera intrinsics and extrinsics,
    in addition to setting stereo parameters.

    Example 1: Setting a custom source frame while specifying the format of the rotation. Note that to set config
    parameters here, it has to be in a child class of CameraInterface.

    .. code-block:: yaml

        {
            "module": "camera.CameraLoader",
            "config": {
                "path": "<args:0>",
                "file_format": "location rotation/value _ _ _ _ _ _",
                "world_frame_change": ["X", "-Z", "Y"],
                "default_cam_param": {
                    "rotation": {
                        "format": "forward_vec"
                    }
                }
            }
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - world_frame_change
          - Can be used if the given camera poses are specified in frames different from the blender
            frame. This parameter changes the world coordinate frame of points and matrices.
            Has to be a list of three strings. Example: ['X', '-Z', 'Y']: Point (1,2,3) will be transformed
            to (1, -3, 2). Default: ["X", "Y", "Z"]. " Available: ['X', 'Y', 'Z', '-X', '-Y', '-Z'].
          - list
        * - local_frame_change
          - Can be used if the given camera poses are specified in frames different from the blender
            frame. This parameter changes the local coordinate frame of matrices. It is currently only
            available when setting camera poses via the cam2world_matrix parameter.
            Has to be a list of three strings. Default: ["X", "Y", "Z"]. " Available: ['X', 'Y', 'Z', '-X', '-Y', '-Z'].
          - list
        * - cam_poses
          - A list of dicts, where each dict specifies one cam pose. See the next table for details about specific
            properties.
          - list
        * - default_cam_param
          - Properties across all cam poses.
          - dict
        * - intrinsics
          - A dictionary containing camera intrinsic parameters. See the last table for details. Default: {}.
          - dict

    **Properties per cam pose**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - location
          - The position of the camera, specified as a list of three values (xyz).
          - mathutils.Vector
        * - rotation/value
          - Specifies the rotation of the camera. Per default rotations are specified as three euler angles. 
          - mathutils.Vector
        * - rotation/format
          - Describes the form in which the rotation is specified. Available: 'euler' (three Euler angles),
            'forward_vec'(specified with a forward vector: the Y-Axis is assumed as Up-Vector), 'look_at' (camera
            will be turned such as it looks at 'value' location, which can be defined as a fixed or sampled XYZ location).
          - string
        * - rotation/inplane_rot
          - A rotation angle in radians around the Z axis. Default: 0.0
          - float
        * - cam2world_matrix
          - 4x4 camera extrinsic matrix. Default: [].
          - list of floats
        * - frame
          - The frame to set the camera pose to.
          - int

    **Intrinsic camera parameters**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cam_K
          - Camera Matrix K. Cx, cy are defined in a coordinate system with (0,0) being the CENTER of the top-left
            pixel - this is the convention e.g. used in OpenCV. 
          - list
        * - shift
          - Principal Point deviation from center. The unit is proportion of the larger image dimension.
          - float
        * - fov
          - The FOV (normally the angle between both sides of the frustum, if fov_is_half is True than its assumed
            to be the angle between forward vector and one side of the frustum). 
          - float
        * - resolution_x
          - Width resolution of the camera.
          - int
        * - resolution_y
          - Height resolution of the camera.
          - int
        * - pixel_aspect_x
          - Pixel aspect ratio x.
          - float
        * - pixel_aspect_y
          - Pixel aspect ratio y.
          - float
        * - clip_start
          - Near clipping.
          - float
        * - clip_end
          - Far clipping.
          - float
        * - stereo_convergence_mode
          - How the two cameras converge (e.g. Off-Axis where both cameras are shifted inwards to converge in the
            convergence plane, or parallel where they do not converge and are parallel). 
          - string.
        * - convergence_distance
          - The convergence point for the stereo cameras (i.e. distance from the projector to the projection
            screen). 
          - float
        * - interocular_distance
          - Distance between the camera pair.
          - float
        * - depth_of_field/focal_object
          - This object will be used as focal point, ideally a empty plane_axes is used here, see BasicEmptyInitializer.
            Using this will automatically activate the depth of field mode. Can not be combined with
            depth_of_field_dist.
          - Provider
        * - depth_of_field/depth_of_field_dist
          - Instead of a focal_object it is possible to use a distance from the camera for the focal plane. More
            control over the scene can be achieved by using a focal_object.
          - float
        * - depth_of_field/fstop
          - The desired amount of blurring, a lower value means more blur and higher value less. Default: 2.4
          - float
        * - depth_of_field/aperture_blades
          - Amount of aperture polygon blades used, to change the shape of the blurred object. Minimum to see an effect
            is three. Default: 0
          - int
        * - depth_of_field/aperture_ratio
          - Change the amount of distortion to simulate the anamorphic bokeh effect. A setting of 1.0 shows no
            distortion, where a number below 1.0 will cause a horizontal distortion, and a higher number
            will cause a vertical distortion. Default: 1.0
          - float
        * - depth_of_field/aperture_rotation_in_rad
          - Rotate the polygonal blades along the facing axis, and will rotate in a clockwise, and
            counter-clockwise fashion in radiant. Default: 0.0
          - float
    """

    def __init__(self, config):
        Module.__init__(self, config)
        # Raise an exception if the deprecated source_frame parameter is used
        if self.config.has_param("source_frame"):
            raise Exception("The parameter `source_frame` parameter is not available anymore. Use `local_frame_change` instead, if you are setting camera poses via `cam2world_matrix`, or use `world_frame_change` instead, if you are setting camera poses via `location` and `rotation`.")
        self.local_frame_change = self.config.get_list("local_frame_change", ["X", "Y", "Z"])
        self.world_frame_change = self.config.get_list("world_frame_change", ["X", "Y", "Z"])

    def _set_cam_intrinsics(self, cam, config):
        """ Sets camera intrinsics from a source with following priority

           1. from config function parameter if defined
           2. from custom properties of cam if set in Loader
           3. default config:
                resolution_x/y: 512
                pixel_aspect_x: 1
                clip_start:   : 0.1
                clip_end      : 1000
                fov           : 0.691111

        :param cam: The camera which contains only camera specific attributes.
        :param config: A configuration object with cam intrinsics.
        """
        if config.is_empty():
            return

        width = config.get_int("resolution_x", bpy.context.scene.render.resolution_x)
        height = config.get_int("resolution_y", bpy.context.scene.render.resolution_y)

        # Clipping
        clip_start = config.get_float("clip_start", cam.clip_start)
        clip_end = config.get_float("clip_end", cam.clip_end)

        if config.has_param("cam_K"):
            if config.has_param("fov"):
                print('WARNING: FOV defined in config is ignored. Mutually exclusive with cam_K')
            if config.has_param("pixel_aspect_x"):
                print('WARNING: pixel_aspect_x defined in config is ignored. Mutually exclusive with cam_K')

            cam_K = np.array(config.get_list("cam_K")).reshape(3, 3).astype(np.float32)

            CameraUtility.set_intrinsics_from_K_matrix(cam_K, width, height, clip_start, clip_end)
        else:
            # Set FOV
            fov = config.get_float("fov", cam.angle)

            # Set Pixel Aspect Ratio
            pixel_aspect_x = config.get_float("pixel_aspect_x", bpy.context.scene.render.pixel_aspect_x)
            pixel_aspect_y = config.get_float("pixel_aspect_y", bpy.context.scene.render.pixel_aspect_y)

            # Set camera shift
            shift_x = config.get_float("shift_x", cam.shift_x)
            shift_y = config.get_float("shift_y", cam.shift_y)

            CameraUtility.set_intrinsics_from_blender_params(fov, width, height, clip_start, clip_end, pixel_aspect_x, pixel_aspect_y, shift_x, shift_y, lens_unit="FOV")

        CameraUtility.set_stereo_parameters(config.get_string("stereo_convergence_mode", cam.stereo.convergence_mode), config.get_float("convergence_distance", cam.stereo.convergence_distance), config.get_float("interocular_distance", cam.stereo.interocular_distance))
        if config.has_param("depth_of_field"):
            depth_of_field_config = Config(config.get_raw_dict("depth_of_field"))
            fstop_value = depth_of_field_config.get_float("fstop", 2.4)
            aperture_blades = depth_of_field_config.get_int("aperture_blades", 0)
            aperture_ratio = depth_of_field_config.get_float("aperture_ratio", 1.0)
            aperture_rotation = depth_of_field_config.get_float("aperture_rotation_in_rad", 0.0)
            if depth_of_field_config.has_param("depth_of_field_dist") and depth_of_field_config.has_param("focal_object"):
                raise RuntimeError("You can only use either depth_of_field_dist or a focal_object but not both!")
            if depth_of_field_config.has_param("depth_of_field_dist"):
                depth_of_field_dist = depth_of_field_config.get_float("depth_of_field_dist")
                CameraUtility.add_depth_of_field(cam, None, fstop_value, aperture_blades,
                                                 aperture_rotation, aperture_ratio, depth_of_field_dist)
            elif depth_of_field_config.has_param("focal_object"):
                focal_object = depth_of_field_config.get_list("focal_object")
                if len(focal_object) != 1:
                    raise RuntimeError(f"There has to be exactly one focal object, use 'random_samples: 1' or change "
                                       f"the selector. Found {len(focal_object)}.")
                CameraUtility.add_depth_of_field(Entity(focal_object[0]), fstop_value, aperture_blades,
                                                 aperture_rotation, aperture_ratio)
            else:
                raise RuntimeError("The depth_of_field dict must contain either a focal_object definition or "
                                   "a depth_of_field_dist")


    def _set_cam_extrinsics(self, config, frame=None):
        """ Sets camera extrinsics according to the config.

        :param frame: Optional, the frame to set the camera pose to.
        :param config: A configuration object with cam extrinsics.
        """
        if config.has_param("frame"):
            frame = config.get_int("frame")

        cam2world_matrix = self._cam2world_matrix_from_cam_extrinsics(config)
        CameraUtility.add_camera_pose(cam2world_matrix, frame)

    def _cam2world_matrix_from_cam_extrinsics(self, config: Config) -> np.ndarray:
        """ Determines camera extrinsics by using the given config and returns them in form of a cam to world frame transformation matrix.

        :param config: The configuration object.
        :return: The 4x4 cam to world transformation matrix.
        """
        if not config.has_param("cam2world_matrix"):
            # Print warning if local_frame_change is used with other attributes than cam2world_matrix
            if self.local_frame_change != ["X", "Y", "Z"]:
                print("Warning: The local_frame_change parameter is at the moment only supported when setting the cam2world_matrix attribute.")
                
            position = change_coordinate_frame_of_point(config.get_vector3d("location", [0, 0, 0]), self.world_frame_change)

            # Rotation
            rotation_format = config.get_string("rotation/format", "euler")
            value = config.get_vector3d("rotation/value", [0, 0, 0])
            # Transform to blender coord frame
            value = change_coordinate_frame_of_point(value, self.world_frame_change)
            
            if rotation_format == "euler":
                # Rotation, specified as euler angles
                rotation_matrix = Euler(value, 'XYZ').to_matrix()
            elif rotation_format == "forward_vec":
                # Convert forward vector to euler angle (Assume Up = Z)
                rotation_matrix = CameraUtility.rotation_from_forward_vec(value)
            elif rotation_format == "look_at":
                # Convert forward vector to euler angle (Assume Up = Z)
                rotation_matrix = CameraUtility.rotation_from_forward_vec(value - position)
            else:
                raise Exception("No such rotation format:" + str(rotation_format))

            if rotation_format == "look_at" or rotation_format == "forward_vec":
                inplane_rot = config.get_float("rotation/inplane_rot", 0.0)
                rotation_matrix = np.matmul(rotation_matrix, Euler((0.0, 0.0, inplane_rot)).to_matrix())

            cam2world_matrix = build_transformation_mat(position, rotation_matrix)
        else:
            cam2world_matrix = np.array(config.get_list("cam2world_matrix")).reshape(4, 4).astype(np.float32)
            cam2world_matrix = change_source_coordinate_frame_of_transformation_matrix(cam2world_matrix, self.local_frame_change)
            cam2world_matrix = change_target_coordinate_frame_of_transformation_matrix(cam2world_matrix, self.world_frame_change)
        return cam2world_matrix
