from src.main.Module import Module
from src.utility.ItemCollection import ItemCollection
from src.utility.Utility import Utility

import mathutils
import bpy
import numpy as np
import os

class CameraModule(Module):
    """
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "source_frame", "Can be used if the given positions and rotations are specified in frames different from the blender frame. Has to be a list of three strings (Allowed values: 'X', 'Y', 'Z', '-X', '-Y', '-Z'). Example: ['X', '-Z', 'Y']: Point (1,2,3) will be transformed to (1, -3, 2)."
       "default_cam_param", "A dict which can be used to specify properties across all cam poses. See the next table for which properties can be set."

    **Properties per cam pose**:

    .. csv-table::
       :header: "Keyword", "Description"

       "location", "The position of the camera, specified as a list of three values (xyz)."
       "rotation", "Specifies the rotation of the camera. rotation_format describes the form in which the rotation is specified. Per default rotations are specified as three euler angles."
       "rotation_format", "Describes the form in which the rotation is specified. Possible values: 'euler': three euler angles, 'forward_vec': Specified with a forward vector (The Y-Axis is assumed as Up-Vector)"
       "shift", "Principal Point deviation from center. The unit is proportion of the larger image dimension"
       "fov", "The FOV (normally the angle between both sides of the frustum, if fov_is_half is true than its assumed to be the angle between forward vector and one side of the frustum)"
       "cam_K", "Camera Matrix K"
       "fov_is_half", "Set to true if the given FOV specifies the angle between forward vector and one side of the frustum"
       "clip_start", "Near clipping"
       "clip_end", "Far clipping"
       "stereo_convergence_mode", "How the two cameras converge (e.g. Off-Axis where both cameras are shifted inwards to converge in the convergence plane, or parallel where they do not converge and are parallel)."
       "stereo_convergence_dist", "The convergence point for the stereo cameras (i.e. distance from the projector to the projection screen)."
       "stereo_interocular_dist", "Distance between the camera pair."
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.source_frame = self.config.get_list("source_frame", ["X", "Y", "Z"])
        self.cam_pose_collection = ItemCollection(self._add_cam_pose, self.config.get_raw_dict("default_cam_param", {}))

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

    def _add_cam_intrinsics(self, config, cam_K=None):
        """ Adds camera intrinsics according to the config file or given camera matrix cam_K.

        :param config: A configuration object with cam intrinsics.
        :param cam_K: Optionally, 3x3 numpy array containing the camera matrix cam_K.
        """
        # Collect camera and camera object
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        width, height = config.get_int("resolution_x", 512), config.get_int("resolution_y", 512)
        if 'loaded_resolution' in cam and not config._has_param('resolution_x'):
            width, height = cam['loaded_resolution']
        bpy.context.scene.render.resolution_x = width
        bpy.context.scene.render.resolution_y = height

        if config._has_param("cam_K"):
            if cam_K != None:
                print('WARNING: Got cam_K from both config and loader. Using config cam_K.')
            cam_K = np.array(config.get_list("cam_K", [])).reshape(3,3).astype(np.float32)

        cam.lens_unit = 'FOV'
        if cam_K is not None:
            if config._has_param("fov"):
                print('WARNING: FOV defined in config is ignored')
            
            # Convert focal lengths to FOV
            cam.angle_y = 2 * np.arctan(height / (2 * cam_K[1,1]))
            cam.angle_x = 2 * np.arctan(width / (2 * cam_K[0, 0]))

            # Convert principal point cx,cy in px to blender cam shift in proportion to larger image dim 
            max_resolution = max(width, height)
            cam.shift_x = -(cam_K[0,2] - width / 2.0) / max_resolution
            cam.shift_y = (cam_K[1, 2] - height / 2.0) / max_resolution
        else:
            # Set FOV (Default value is the same as the default blender value)
            cam.angle = config.get_float("fov", 0.691111)
            # FOV is sometimes also given as the angle between forward vector and one side of the frustum
            if config.get_bool("fov_is_half", False):
                cam.angle *= 2
        # Clipping (Default values are the same as default blender values)
        cam.clip_start = config.get_float("clip_start", 0.1)
        cam.clip_end = config.get_float("clip_end", 1000)

    def _add_cam_pose(self, config, H_cam2world=None, cam_K=None):
        """ Adds new cam pose + intrinsics according to the given configuration.

        :param config: A configuration object which contains all parameters relevant for the new cam pose.
        :param H_cam2world: Optionally, 4x4 numpy array defining homogenous trafo from camera to world coordinates. 
        :param cam_K: Optionally, 3x3 numpy array containing the camera matrix cam_K.
        """

        self._add_cam_intrinsics(config, cam_K)

        # Collect camera object
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        cam_ob.location = Utility.transform_point_to_blender_coord_frame(config.get_list("location", [0, 0, 0]), self.source_frame)

        # Rotation
        rotation_format = config.get_string("rotation_format", "euler")
        rotation = config.get_list("rotation", [0, 0, 0])
        if rotation_format == "euler":
            # Rotation, specified as euler angles
            cam_ob.rotation_euler = Utility.transform_point_to_blender_coord_frame(rotation, self.source_frame)
        elif rotation_format == "forward_vec":
            # Rotation, specified as forward vector
            forward_vec = mathutils.Vector(Utility.transform_point_to_blender_coord_frame(rotation, self.source_frame))
            # Convert forward vector to euler angle (Assume Up = Z)
            cam_ob.rotation_euler = forward_vec.to_track_quat('-Z', 'Y').to_euler()
        else:
            raise Exception("No such rotation_format:" + str(rotation_format))

        if H_cam2world is not None:
            # Set homogenous camera pose from input parameter H_cam2world
            cam_ob.matrix_world = H_cam2world
            cam_ob.scale = [1,-1,-1] # fix orientation OpenCV to Blender

        # How the two cameras converge (e.g. Off-Axis where both cameras are shifted inwards to converge in the
        # convergence plane, or parallel where they do not converge and are parallel)
        cam.stereo.convergence_mode = config.get_string("stereo_convergence_mode", "OFFAXIS")
        # The convergence point for the stereo cameras (i.e. distance from the projector to the projection screen) (Default value is the same as the default blender value)
        cam.stereo.convergence_distance = config.get_float("convergence_distance", 1.95)
        # Distance between the camera pair (Default value is the same as the default blender value)
        cam.stereo.interocular_distance = config.get_float("interocular_distance", 0.065)

        # Store new cam pose as next frame
        frame_id = bpy.context.scene.frame_end
        self._insert_key_frames(cam, cam_ob, frame_id)
        bpy.context.scene.frame_end = frame_id + 1
