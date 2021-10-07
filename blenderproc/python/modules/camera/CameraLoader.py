import bpy

from blenderproc.python.modules.camera.CameraInterface import CameraInterface
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.modules.utility.ItemCollection import ItemCollection


class CameraLoader(CameraInterface):
    """
    Loads camera poses from the configuration and sets them as separate keypoints.
    Camera poses can be specified either directly inside the config or in an extra file.

    Example 1: Loads camera poses from file <args:0>, followed by the pose file format and setting the fov in radians.

    .. code-block:: yaml

        {
          "module": "camera.CameraLoader",
          "config": {
            "path": "<args:0>",
            "file_format": "location rotation/value",
            "intrinsics": {
              "fov": 1
            }
          }
        }

    Example 2: More examples for parameters in "intrinsics". Here cam_K is a camera matrix. Check
    CameraInterface for more info on "intrinsics".

    .. code-block:: yaml

        "intrinsics": {
          "fov_is_half": true,
          "interocular_distance": 0.05,
          "stereo_convergence_mode": "PARALLEL",
          "convergence_distance": 0.00001,
          "cam_K": [650.018, 0, 637.962, 0, 650.018, 355.984, 0, 0 ,1],
          "resolution_x": 1280,
          "resolution_y": 720
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cam_poses
          - Optionally, a list of dicts, where each dict specifies one cam pose. See CameraInterface for which
            properties can be set. Default: [].
          - list of dicts
        * - path
          - Optionally, a path to a file which specifies one camera position per line. The lines has to be formatted
            as specified in 'file_format'. Default: "".
          - string
        * - file_format
          - A string which specifies how each line of the given file is formatted. The string should contain the
            keywords of the corresponding properties separated by a space. See next table for allowed properties.
            Default: "".
          - string
        * - default_cam_param
          - A dict which can be used to specify properties across all cam poses. Default: {}.
          - dict
        * - intrinsics
          - A dictionary containing camera intrinsic parameters. Default: {}.
          - dict
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
        self._set_cam_extrinsics(config)
