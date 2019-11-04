from src.camera.CameraModule import CameraModule
import mathutils
import bpy

from src.utility.Utility import Utility
import h5py
import os

class CameraHdfLoader(CameraModule):
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
        file_format = self.config.get_string("file_format", "").split()

        cam_poses = []
        for i in range(1, 1+len(os.listdir(self.config.get_string("path")))):
            with h5py.File(os.path.join(self.config.get_string("path"), str(i) + ".hdf5"), 'r') as data:
                cam_poses.append(self.cam_pose_collection._parse_arguments_from_file(list(data["campose"]), file_format, self.number_of_arguments_per_parameter))

        self.cam_pose_collection.add_items_from_dicts(cam_poses)



