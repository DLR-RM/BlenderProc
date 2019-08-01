from src.main.Module import Module
import bpy
import h5py
import os
from src.utility.Utility import Utility
import imageio

import numpy as np

class Hdf5Writer(Module):

    def __init__(self, config):
        Module.__init__(self, config)

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

                    if output_type["key"] == "seg": # This is so far mandatory for seg maps, and shouldn't be optional, i.e. an option in the config file
                        self.refine_seg_map(data)

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

    def refine_seg_map(self, data):

        def get_neighbors(i, j):
            neighbors = ([[i + 1, j], [i, j + 1], [i + 1, j + 1], [i - 1, j], [i, j - 1], [i - 1, j - 1], [i + 1, j - 1], [i - 1, j + 1]])
            return np.array([np.array(n) for n in neighbors])

        def remove_noise(a, noise_indices):
            for row in noise_indices:
                neighbors = get_neighbors(row[0], row[1])
                curr_val = a[row[0]][row[1]][0]
                
                neighbor_vals = [a[neighbor[0]][neighbor[1]] for neighbor in neighbors]
                neighbor_vals = np.unique(np.array([np.array(row) for row in neighbor_vals]))
                
                min = 10000000000
                min_idx = 0

                for idx, n in enumerate(neighbor_vals):
                    if n - curr_val <= min:
                        min = n - curr_val
                        min_idx = idx
                
                new_val = neighbor_vals[min_idx]
                a[row[0]][row[1]] = np.array([new_val, new_val, new_val])

        # The map was scaled to be ranging along the entire 16 bit color depth, and this is the scaling down operation that should remove some noise or deviations
        data = ((data * 37) / (2**16)) # datassuming data 16 bit color depth
        data = data.astype(np.int32)
        b, counts = np.unique(data.flatten(), return_counts=True)

        # Removing further noise where there are some stray pixel values with very small counts, by assigning them to their closest (numerically, since this deviation is a
        # result of some numerical operation) neighbor.
        hist = sorted((np.asarray((b, counts)).T), key= lambda x: x[1])
        noise_vals = [h[0] for h in hist if h[1] <= 100] # Assuming the stray pixels wouldn't have a count of more than 100
        noise_indices = np.argwhere(np.isin(data, noise_vals))

        remove_noise(data, noise_indices)
