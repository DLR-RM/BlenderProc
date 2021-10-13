from blenderproc.python.writer.WriterUtility import WriterUtility

import os

import bpy
import h5py
import numpy as np

from blenderproc.python.modules.main.GlobalStorage import GlobalStorage
from blenderproc.python.modules.writer.WriterInterface import WriterInterface
from blenderproc.python.utility.Utility import Utility


class Hdf5Writer(WriterInterface):
    """ For each key frame merges all registered output files into one hdf5 file.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - append_to_existing_output
          - If true, the names of the output hdf5 files will be chosen in a way such that there are no collisions
            with already existing hdf5 files in the output directory. Default: False
          - bool
        * - compression
          - The compression technique that should be used when storing data in a hdf5 file.
          - string
        * - delete_temporary_files_afterwards
          - True, if all temporary files should be deleted after merging. Default value: True.
          - bool
        * - stereo_separate_keys
          - If true, stereo images are saved as two separate images \*_0 and \*_1. Default: False
            (stereo images are combined into one np.array (2, ...)).
          - bool
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        self._append_to_existing_output = self.config.get_bool("append_to_existing_output", False)
        self._output_dir = self._determine_output_dir(False)

    def run(self):
        if self._avoid_output:
            print("Avoid output is on, no output produced!")
            return

        if self._append_to_existing_output:
            frame_offset = 0
            # Look for hdf5 file with highest index
            for path in os.listdir(self._output_dir):
                if path.endswith(".hdf5"):
                    index = path[:-len(".hdf5")]
                    if index.isdigit():
                        frame_offset = max(frame_offset, int(index) + 1)
        else:
            frame_offset = 0

        # Go through all frames
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):

            # Create output hdf5 file
            hdf5_path = os.path.join(self._output_dir, str(frame + frame_offset) + ".hdf5")
            with h5py.File(hdf5_path, "w") as f:

                if not GlobalStorage.is_in_storage("output"):
                    print("No output was designed in prior models!")
                    return
                # Go through all the output types
                print("Merging data for frame " + str(frame) + " into " + hdf5_path)

                for output_type in GlobalStorage.get("output"):
                    # Build path (path attribute is format string)
                    file_path = output_type["path"]
                    if '%' in file_path:
                        file_path = file_path % frame

                    # Check if file exists
                    if not os.path.exists(file_path):
                        # If not try stereo suffixes
                        path_l, path_r = WriterUtility._get_stereo_path_pair(file_path)
                        if not os.path.exists(path_l) or not os.path.exists(path_r):
                            raise Exception("File not found: " + file_path)
                        else:
                            use_stereo = True
                    else:
                        use_stereo = False

                    if use_stereo:
                        path_l, path_r = WriterUtility._get_stereo_path_pair(file_path)

                        img_l, new_key, new_version = self._load_and_postprocess(path_l, output_type["key"],
                                                                                   output_type["version"])
                        img_r, new_key, new_version = self._load_and_postprocess(path_r, output_type["key"],
                                                                                   output_type["version"])

                        if self.config.get_bool("stereo_separate_keys", False):
                            WriterUtility._write_to_hdf_file(f, new_key + "_0", img_l)
                            WriterUtility._write_to_hdf_file(f, new_key + "_1", img_r)
                        else:
                            data = np.array([img_l, img_r])
                            WriterUtility._write_to_hdf_file(f, new_key, data)

                    else:
                        data, new_key, new_version = self._load_and_postprocess(file_path, output_type["key"],
                                                                                output_type["version"])

                        WriterUtility._write_to_hdf_file(f, new_key, data)

                    WriterUtility._write_to_hdf_file(f, new_key + "_version", np.string_([new_version]))

                blender_proc_version = Utility.get_current_version()
                if blender_proc_version:
                    WriterUtility._write_to_hdf_file(f, "blender_proc_version", np.string_(blender_proc_version))

