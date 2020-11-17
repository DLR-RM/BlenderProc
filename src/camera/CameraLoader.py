import bpy

from src.camera.CameraInterface import CameraInterface
from src.utility.Config import Config
from src.utility.ItemCollection import ItemCollection


class CameraLoader(CameraInterface):
    """ Loads camera poses from the configuration and sets them as separate keypoints.
        Camera poses can be specified either directly inside the config or in an extra file.

        Example 1: Loads camera poses from file <args:0>, followed by the pose file format and setting the fov in radians.

        {
          "module": "camera.CameraLoader",
          "config": {
            "path": "<args:0>",
            "file_format": "location rotation/value",
            "default_cam_param": {
              "fov": 1
            }
          }
        }

        Example 2: More examples for parameters in "default_cam_param". Here cam_K is a camera matrix. Check
                   CameraInterface for more info on "default_cam_param".

        "default_cam_param": {
          "fov_is_half": true,
          "interocular_distance": 0.05,
          "stereo_convergence_mode": "PARALLEL",
          "convergence_distance": 0.00001,
          "cam_K": [650.018, 0, 637.962, 0, 650.018, 355.984, 0, 0 ,1],
          "resolution_x": 1280,
          "resolution_y": 720
        }

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "cam_poses", "Optionally, a list of dicts, where each dict specifies one cam pose. See CameraInterface for which "
                    "properties can be set. Type: list of dicts. Default: []."
       "path", "Optionally, a path to a file which specifies one camera position per line. The lines has to be "
               "formatted as specified in 'file_format'. Type: string. Default: ""."
       "file_format", "A string which specifies how each line of the given file is formatted. The string should contain "
                      "the keywords of the corresponding properties separated by a space. See next table for allowed "
                      "properties. Type: string. Default: ""."
       "default_cam_param", "A dict which can be used to specify properties across all cam poses. Type: dict. Default: {}."
       "intrinsics", "A dictionary containing camera intrinsic parameters. Type: dict. Default: {}."
    """

    def __init__(self, config):
        CameraInterface.__init__(self, config)
        # A dict specifying the length of parameters that require more than one argument. If not specified, 1 is assumed.
        self.number_of_arguments_per_parameter = {
            "location": 3,
            "rotation/value": 3,
            "cam2world_matrix": 16
        }
        self.cam_pose_collection = ItemCollection(self._add_cam_pose, self.config.get_raw_dict("default_cam_param", {}))

    def run(self):
        # Set intrinsics
        self._set_cam_intrinsics(bpy.context.scene.camera.data, Config(self.config.get_raw_dict("intrinsics", {})))

        self.cam_pose_collection.add_items_from_dicts(self.config.get_list("cam_poses", []))
        self.cam_pose_collection.add_items_from_file(self.config.get_string("path", ""),
                                                     self.config.get_string("file_format", ""),
                                                     self.number_of_arguments_per_parameter)

    def _add_cam_pose(self, config):
        """ Adds new cam pose + intrinsics according to the given configuration.

        :param config: A configuration object which contains all parameters relevant for the new cam pose.
        """

        # Collect camera object
        cam_ob = bpy.context.scene.camera

        # Set extrinsics from config
        self._set_cam_extrinsics(cam_ob, config)