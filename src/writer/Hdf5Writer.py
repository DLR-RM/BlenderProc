import os

import bpy
import h5py
import numpy as np

from src.main.GlobalStorage import GlobalStorage
from src.writer.WriterInterface import WriterInterface
from src.utility.Utility import Utility


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
        * - avoid_rendering
          - If true, exit. Default: False.
          - bool
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        self._avoid_rendering = config.get_bool("avoid_rendering", False)

    def run(self):
        if self._avoid_rendering:
            print("Avoid rendering is on, no output produced!")
            return

        if self.config.get_bool("append_to_existing_output", False):
            frame_offset = 0
            # Look for hdf5 file with highest index
            for path in os.listdir(self._determine_output_dir(False)):
                if path.endswith(".hdf5"):
                    index = path[:-len(".hdf5")]
                    if index.isdigit():
                        frame_offset = max(frame_offset, int(index) + 1)
        else:
            frame_offset = 0

        # Go through all frames
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):

            # Create output hdf5 file
            hdf5_path = os.path.join(self._determine_output_dir(False), str(frame + frame_offset) + ".hdf5")
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
                        path_l, path_r = self._get_stereo_path_pair(file_path)
                        if not os.path.exists(path_l) or not os.path.exists(path_r):
                            raise Exception("File not found: " + file_path)
                        else:
                            use_stereo = True
                    else:
                        use_stereo = False

                    if use_stereo:
                        path_l, path_r = self._get_stereo_path_pair(file_path)

                        img_l, new_key, new_version = self._load_and_postprocess(path_l, output_type["key"],
                                                                                   output_type["version"])
                        img_r, new_key, new_version = self._load_and_postprocess(path_r, output_type["key"],
                                                                                   output_type["version"])

                        if self.config.get_bool("stereo_separate_keys", False):
                            self._write_to_hdf_file(f, new_key + "_0", img_l)
                            self._write_to_hdf_file(f, new_key + "_1", img_r)
                        else:
                            data = np.array([img_l, img_r])
                            self._write_to_hdf_file(f, new_key, data)

                    else:
                        data, new_key, new_version = self._load_and_postprocess(file_path, output_type["key"],
                                                                                output_type["version"])

                        self._write_to_hdf_file(f, new_key, data)

                    self._write_to_hdf_file(f, new_key + "_version", np.string_([new_version]))

    def _write_to_hdf_file(self, file, key, data):
        """ Adds the given data as a new entry to the given hdf5 file.

        :param file: The hdf5 file handle.
        :param key: The key at which the data should be stored in the hdf5 file. Type: string.
        :param data: The data to store.
        """
        if data.dtype.char == 'S':
            file.create_dataset(key, data=data, dtype=data.dtype)
        else:
            file.create_dataset(key, data=data, compression=self.config.get_string("compression", 'gzip'))

    def _get_stereo_path_pair(self, file_path):
        """
        Returns stereoscopic file path pair for a given "normal" image file path.

        :param file_path: The file path of a single image. Type: string.
        :return: The pair of file paths corresponding to the stereo images,
        """
        path_split = file_path.split(".")
        path_l = "{}_L.{}".format(path_split[0], path_split[1])
        path_r = "{}_R.{}".format(path_split[0], path_split[1])

        return path_l, path_r
