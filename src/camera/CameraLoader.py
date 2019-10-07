from src.camera.CameraModule import CameraModule
from src.main.Module import Module
import mathutils
import bpy

from src.utility.Utility import Utility


class CameraLoader(CameraModule):
    """
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "cam_poses", "Optionally, a list of dicts, where each dict specifies one cam pose. See the next table for which properties can be set."
       "path", "Optionally, a path to a file which specifies one camera position per line. The lines has to be formatted as specified in 'file_format'."
       "file_format", "A string which specifies how each line of the given file is formatted. The string should contain the keywords of the corresponding properties separated by a space. See next table for allowed properties."
       "source_frame", "Can be used if the given positions and rotations are specified in frames different from the blender frame. Has to be a list of three strings (Allowed values: 'X', 'Y', 'Z', '-X', '-Y', '-Z'). Example: ['X', '-Z', 'Y']: Point (1,2,3) will be transformed to (1, -3, 2)."
       "default_cam_param", "A dict which can be used to specify properties across all cam poses. See the next table for which properties can be set."

    **Properties per cam pose**:

    .. csv-table::
       :header: "Keyword", "Description"

       "location", "The position of the camera, specified as a list of three values (xyz)."
       "rotation_euler", "The rotation of the camera, specified as a list of three euler angles."
       "rotation_forward_vector", "The rotation of the camera, specified with a forward vector (The z-Axis is assumed as Up-Vector). The forward vector has to be specified as a list of three values (xyz)."
       "fov", "The full FOV (angle between both sides of the frustum)"
       "fov_half", "Half of the FOV (the angle between forward vector and one side of the frustum)"
       "clip_start", "Near clipping"
       "clip_end", "Far clipping"
    """

    def __init__(self, config):
        CameraModule.__init__(self, config)
        self.file_format = self.config.get_string("file_format", "").split()
        # A dict which holds the number of values per attribute. If not specified, 1 is assumed.
        self.cam_attribute_length = {
            "location": 3,
            "rotation_euler": 3,
            "rotation_forward_vector": 3
        }
        self.file_format_length = sum([self._length_of_attribute(attribute) for attribute in self.file_format])
        self.source_frame = self.config.get_list("source_frame", ["X", "Y", "Z"])

    def run(self):
        """ Loads camera poses from the configuration and sets them as separate keypoints.

        Camera poses can be specified either directly inside a the config or in an extra file.
        """
        # Collect camera and camera object
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        # Start with next frame
        frame_id = bpy.context.scene.frame_end + 1

        # Add cam poses configured in the config
        cam_poses = self.config.get_list("cam_poses", [])
        for cam_pose in cam_poses:
            # Init cam pose
            self._initialize_cam_pose(cam, cam_ob)
            # Set cam pose using the configured dict
            self._set_cam_from_config(cam, cam_ob, cam_pose)
            # Insert key frames
            self._insert_key_frames(cam, cam_ob, frame_id)

            # Write new cam pose to output
            self._write_cam_pose_to_file(frame_id, cam, cam_ob)
            frame_id += 1

        # Add cam poses configured in a file
        path = self.config.get_string("path", "")
        for cam_pose in self._collect_cam_poses_from_file(path):
            # Init cam pose
            self._initialize_cam_pose(cam, cam_ob)
            # Set cam pose using arguments configured in one line of the file
            self._set_cam_from_file_args(cam, cam_ob, cam_pose)
            # Insert key frames
            self._insert_key_frames(cam, cam_ob, frame_id)

            # Write new cam pose to output
            self._write_cam_pose_to_file(frame_id, cam, cam_ob)
            frame_id += 1

        # Set frame end to the last written frame
        bpy.context.scene.frame_end = frame_id - 1
        # Make sure frame_start is 1 (By setting frame_end to 0 in the Initializer module, blender also sets frame_start to 0)
        bpy.context.scene.frame_start = 1
        self._register_cam_pose_output()

    def _initialize_cam_pose(self, cam, cam_ob):
        """ Sets the attributes of the given camera to the configured default parameters.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        """
        # Default attribute values (same as default values in blender)
        base_config = {
            "fov": 0.691111,
            "clip_start": 0.1,
            "clip_end": 1000
        }
        # Overwrite default attribute values with configured default parameters
        config = Utility.merge_dicts(self.config.get_raw_dict("default_cam_param", {}), base_config)

        # Make sure we use FOV
        cam.lens_unit = 'FOV'
        # Set camera attributes
        self._set_cam_from_config(cam, cam_ob, config)

    def _set_cam_from_file_args(self, cam, cam_ob, cam_args):
        """ Sets the camera parameters based on the arguments specified in one line of the configured file.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param cam_args: A list of arguments retrieved from one line out of the configured file.
        """
        # Go through all configured attributes
        for attribute in self.file_format:
            # Set the current attribute, use the next N arguments
            self._set_attribute(cam, cam_ob, attribute, cam_args[:self._length_of_attribute(attribute)])
            # Skip the arguments used for the current attribute
            cam_args = cam_args[self._length_of_attribute(attribute):]

    def _collect_cam_poses_from_file(self, path):
        """ Reads in all lines of the given file and returns them as a list of lists of arguments

        This method also checks is the lines match the configured file format.

        :param path: The path of the file.
        :return: A list of lists of arguments
        """
        cam_poses = []
        if path != "":
            with open(Utility.resolve_path(path)) as f:
                lines = f.readlines()
                # remove all empty lines
                lines = [line for line in lines if len(line.strip()) > 3]

                for line in lines:
                    # Split line into separate arguments
                    cam_args = line.strip().split()
                    # Make sure the arguments match the configured file format
                    if len(cam_args) != self.file_format_length:
                        raise Exception("A line in the given cam pose file does not match the configured file format:\n" + line.strip() + " (Number of values: " + str(len(cam_args)) + ")\n" + str(self.file_format) + " (Number of values: " + str(self.file_format_length) + ")")

                    cam_poses.append([float(x) for x in cam_args])

        return cam_poses

    def _set_cam_from_config(self, cam, cam_ob, config):
        """ Sets cam attributes based on the given config dict.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: A dict where the key is the attribute name and the value is the value to set this attribute to.
        """
        # Go through all key/value pairs of the given dict and set the corresponding attributes
        for attribute_name, value in config.items():
            self._set_attribute(cam, cam_ob, attribute_name, value)

    def _length_of_attribute(self, attribute):
        """ Returns, how many arguments the given attribute expects.

        :param attribute: The name of the attribute
        :return: The expected number of arguments.
        """
        # If the length is not set, return 1
        if attribute in self.cam_attribute_length:
            return self.cam_attribute_length[attribute]
        else:
            return 1

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
        elif attribute_name == "_":
            # Just skip this argument
            pass
        else:
            raise Exception("No such attribute: " + attribute_name)

    def _insert_key_frames(self, cam, cam_ob, frame_id):
        """ Insert key frames for all relevant camera attributes.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param frame_id: The frame number where key frames should be inserted.
        """
        cam.keyframe_insert(data_path='clip_start', frame=frame_id)
        cam.keyframe_insert(data_path='clip_end', frame=frame_id)
        cam_ob.keyframe_insert(data_path='location', frame=frame_id)
        cam_ob.keyframe_insert(data_path='rotation_euler', frame=frame_id)

