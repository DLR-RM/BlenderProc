from src.main.Module import Module
import bpy
import h5py
import os
from src.utility.Utility import Utility
import imageio


class Hdf5Writer(Module):

    def __init__(self, config):
        Module.__init__(self, config)

        self.postprocessing_modules_per_output = {}
        module_configs = config.get_raw_dict("postprocessing_modules", {})
        for output_key in module_configs:
            self.postprocessing_modules_per_output[output_key] = Utility.initialize_modules(module_configs[output_key], {})

    def run(self):
        output_dir = Utility.resolve_path(self.config.get_string("output_dir"))

        # Go through all frames
        for frame in range(1, bpy.context.scene.frame_end + 1):

            # Create output hdf5 file
            hdf5_path = os.path.join(output_dir, str(frame) + ".hdf5")
            with h5py.File(hdf5_path, "w") as f:

                # Go through all the output types
                print("Merging data for frame " + str(frame) + " into " + hdf5_path)
                for output_type in bpy.context.scene["output"]:

                    # Build path (path attribute is format string)
                    file_path = output_type["path"] % frame

                    data = self._load_file(Utility.resolve_path(file_path))

                    data = self._apply_postprocessing(output_type["key"], data)

                    print("Key: " + output_type["key"] + " - shape: " + str(data.shape) + " - dtype: " + str(data.dtype) + " - path: " + file_path)

                    f.create_dataset(output_type["key"], data=data, compression=self.config.get_string("compression", 'gzip'))

                    if self.config.get_bool("delete_original_files_afterwards", True):
                        os.remove(file_path)

    def _load_file(self, file_path):
        if not os.path.exists(file_path):
            raise Exception("File not found: " + file_path)

        file_ending = file_path[file_path.rfind(".") + 1:].lower()

        if file_ending in ["exr", "png", "jpg"]:
            return self._load_image(file_path)
        else:
            raise NotImplementedError("File with ending " + file_ending + " cannot be loaded.")

    def _load_image(self, file_path):
        return imageio.imread(file_path)[:, :, :3]

    def _apply_postprocessing(self, output_key, data):
        if output_key in self.postprocessing_modules_per_output:
            for module in self.postprocessing_modules_per_output[output_key]:
                data = module.run(data)

        return data

