from src.camera.CameraModule import CameraModule
import mathutils
import bpy

from src.utility.ItemCollection import ItemCollection
from src.utility.Utility import Utility


class CameraLoader(CameraModule):
    """ Loads camera poses from the configuration and sets them as separate keypoints.

    Camera poses can be specified either directly inside a the config or in an extra file.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "cam_poses", "Optionally, a list of dicts, where each dict specifies one cam pose. See the next table for which properties can be set."
       "path", "Optionally, a path to a file which specifies one camera position per line. The lines has to be formatted as specified in 'file_format'."
       "file_format", "A string which specifies how each line of the given file is formatted. The string should contain the keywords of the corresponding properties separated by a space. See next table for allowed properties."
    """

    def __init__(self, config):
        CameraModule.__init__(self, config)
        # A dict specifying the length of parameters that require more than one argument. If not specified, 1 is assumed.
        self.number_of_arguments_per_parameter = {
            "location": 3,
            "rotation/value": 3
        }
        self.cam_pose_collection = ItemCollection(self._add_cam_pose, self.config.get_raw_dict("default_cam_param", {}))

    def run(self):
        self.cam_pose_collection.add_items_from_dicts(self.config.get_list("cam_poses", []))
        self.cam_pose_collection.add_items_from_file(self.config.get_string("path", ""), self.config.get_string("file_format", ""), self.number_of_arguments_per_parameter)

    def _add_cam_pose(self, config):
        """ Adds new cam pose + intrinsics according to the given configuration.

        :param config: A configuration object which contains all parameters relevant for the new cam pose.
        """

        # Collect camera object
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        # Set intrinsics and extrinsics from config
        self._set_cam_intrinsics(cam, config)
        self._set_cam_extrinsics(cam_ob, config)

        # Store new cam pose as next frame
        frame_id = bpy.context.scene.frame_end
        self._insert_key_frames(cam, cam_ob, frame_id)
        bpy.context.scene.frame_end = frame_id + 1
