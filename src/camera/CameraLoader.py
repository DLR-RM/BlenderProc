from src.camera.CameraModule import CameraModule
import mathutils
import bpy

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
            "rotation": 3
        }

    def run(self):
        self.cam_pose_collection.add_items_from_dicts(self.config.get_list("cam_poses", []))
        self.cam_pose_collection.add_items_from_file(self.config.get_string("path", ""), self.config.get_string("file_format", ""), self.number_of_arguments_per_parameter)


