from blenderproc.python.modules.writer.WriterInterface import WriterInterface
from blenderproc.python.writer.BopWriterUtility import write_bop

import os

class BopWriter(WriterInterface):
    """ Saves the synthesized dataset in the BOP format. The dataset is split
        into chunks which are saved as individual "scenes". For more details
        about the BOP format, visit the BOP toolkit docs:
        https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md

    **Attributes per object**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - dataset
          - Only save annotations for objects of the specified bop dataset. Saves all object poses if not defined.
            Default: ''
          - string
        * - append_to_existing_output
          - If true, the new frames will be appended to the existing ones. Default: False
          - bool
        * - save_world2cam
          - If true, camera to world transformations "cam_R_w2c", "cam_t_w2c" are saved in scene_camera.json. Default: True
          - bool
        * - ignore_dist_thres
          - Distance between camera and object after which object is ignored. Mostly due to failed physics. Default: 100.
          - float
        * - depth_scale
          - Multiply the uint16 output depth image with this factor to get depth in mm. Used to trade-off between depth accuracy 
            and maximum depth value. Default corresponds to 65.54m maximum depth and 1mm accuracy. Default: 1.0
          - float
        * - m2mm
          - Original bop annotations and models are in mm. If true, we convert the gt annotations to mm here. This
            is needed if BopLoader option mm2m is used. Default: True
          - bool
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        
        # Parse configuration.
        self._dataset = self.config.get_string("dataset", "")

        self._append_to_existing_output = self.config.get_bool("append_to_existing_output", False)
        
        # Save world to camera transformation
        self._save_world2cam = self.config.get_bool("save_world2cam", True)

        # Distance in meteres to object after which it is ignored. Mostly due to failed physics.
        self._ignore_dist_thres = self.config.get_float("ignore_dist_thres", 100.)

        # Multiply the output depth image with this factor to get depth in mm.
        self._depth_scale = self.config.get_float("depth_scale", 1.0)

        # Output translation gt in mm
        self._mm2m = self.config.get_bool("m2mm", True)

    def run(self):
        """ Stores frames and annotations for objects from the specified dataset.
        """

        if self._avoid_output:
            print("Avoid output is on, no output produced!")
        else:
            write_bop(output_dir = os.path.join(self._determine_output_dir(False), 'bop_data'),
                                dataset = self._dataset, 
                                append_to_existing_output = self._append_to_existing_output, 
                                depth_scale = self._depth_scale, 
                                save_world2cam = self._save_world2cam, 
                                ignore_dist_thres = self._ignore_dist_thres, 
                                m2mm = self._mm2m)