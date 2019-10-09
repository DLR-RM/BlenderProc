from src.main.Module import Module
from src.utility.Utility import Utility

import mathutils
import bpy
import numpy as np
import os


class CameraModule(Module):

    def __init__(self, config):
        Module.__init__(self, config)
        self.source_frame = self.config.get_list("source_frame", ["X", "Y", "Z"])

    def _write_cam_pose_to_file(self, frame, cam, cam_ob, room_id=-1):
        """ Determines the current pose of the given camera and writes it to a .npy file.

        :param frame: The current frame number, used for naming the output file.
        :param cam: The camera.
        :param cam_ob: The camera object.
        :param room_id: The id of the room which contains the camera (optional)
        """
        cam_pose = []
        # Location
        cam_pose.extend(cam_ob.location[:])
        # Orientation
        cam_pose.extend(cam_ob.rotation_euler[:])
        # FOV
        cam_pose.extend([cam.angle_x, cam.angle_y])
        # Room
        cam_pose.append(room_id)
        np.save(os.path.join(self.output_dir, "campose_" + ("%04d" % frame)), cam_pose)

    def _register_cam_pose_output(self):
        """ Registers the written cam pose files as an output """
        self._register_output("campose_", "campose", ".npy", "1.0.0")

    def _initialize_cam_pose(self, cam, cam_ob):
        """ Sets the attributes of the given camera to the configured default parameters.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        """
        # Default attribute values (same as default values in blender)
        base_config = {
            "fov": 0.691111,
            "clip_start": 0.1,
            "clip_end": 1000,
            "stereo_convergence_mode": "OFFAXIS",
            "stereo_convergence_dist": 1.95,
            "stereo_interocular_dist": 0.065
        }
        # Overwrite default attribute values with configured default parameters
        config = Utility.merge_dicts(self.config.get_raw_dict("default_cam_param", {}), base_config)

        # Make sure we use FOV
        cam.lens_unit = 'FOV'
        # Set camera attributes
        self._set_cam_from_config(cam, cam_ob, config)

    def _set_cam_from_config(self, cam, cam_ob, config):
        """ Sets cam attributes based on the given config dict.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: A dict where the key is the attribute name and the value is the value to set this attribute to.
        """
        # Go through all key/value pairs of the given dict and set the corresponding attributes
        for attribute_name, value in config.items():
            self._set_attribute(cam, cam_ob, attribute_name, value)

    def _set_attribute(self, cam, cam_ob, attribute_name, value):
        """ Sets the value of the given attribute.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param attribute_name: The name of the attribute to change.
        :param value: The value to set.
        """
        # Make sure value is always a list
        if not isinstance(value, list):
            value = [value]

        if attribute_name == "fov":
            # The full FOV (angle between both sides of the frustum)
            cam.angle = value[0]
        elif attribute_name == "fov_half":
            # FOV is sometimes also given as the angle between forward vector and one side of the frustum
            cam.angle = value[0] * 2
        elif attribute_name == "clip_start":
            # Near clipping
            cam.clip_start = value[0]
        elif attribute_name == "clip_end":
            # Far clipping
            cam.clip_end = value[0]
        elif attribute_name == "location":
            # Position (x,y,z)
            cam_ob.location = Utility.transform_point_to_blender_coord_frame(value, self.source_frame)
        elif attribute_name == "rotation_euler":
            # Rotation, specified as euler angles
            cam_ob.rotation_euler = Utility.transform_point_to_blender_coord_frame(value, self.source_frame)
        elif attribute_name == "rotation_forward_vector":
            # Rotation, specified as forward vector
            forward_vec = mathutils.Vector(Utility.transform_point_to_blender_coord_frame(value, self.source_frame))
            # Convert forward vector to euler angle (Assume Up = Z)
            cam_ob.rotation_euler = forward_vec.to_track_quat('-Z', 'Y').to_euler()
        elif attribute_name == "stereo_convergence_mode":
            cam.stereo.convergence_mode = value[0]
        elif attribute_name == "stereo_convergence_dist":
            cam.stereo.convergence_distance = value[0]
        elif attribute_name == "stereo_interocular_dist":
            cam.stereo.interocular_distance = value[0]
        elif attribute_name == "_":
            # Just skip this argument
            pass
        else:
            raise Exception("No such attribute: " + attribute_name)
