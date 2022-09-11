"""Allows to write a set of rendering as a gif animation for quick visualization."""

from typing import Dict, List, Union
import os

import bpy
import numpy as np
from PIL import Image

from blenderproc.scripts.visHdf5Files import vis_data
from blenderproc.python.utility.Utility import Utility


def write_gif_animation(
        output_dir_path: str,
        output_data_dict: Dict[str, List[Union[np.ndarray, list, dict]]],
        append_to_existing_output: bool = False,
        frame_duration_in_ms: int = 50,
        reverse_animation: bool = False):
    """
    Generates a .gif file animation out of rendered frames

    :param output_dir_path: The directory path in which the gif animation folder will be saved
    :param output_data_dict: The data dictionary which was produced by the render method.
    :param append_to_existing_output: If this is True, the output_dir_path folder will be scanned for pre-existing
                            files of the name #_animation.gif and the number of newly added files will
                            start right where the last run left off.
    :param frame_duration_in_ms: Duration of each frame in the animation in milliseconds.
    :param reverse_animation: If this is True, the order of the frames will be reversed.
    """

    # Generates subdirectory for .gif files
    output_dir_path = _GifWriterUtility.provide_directory(output_dir_path)

    # From WriterUtility.py
    amount_of_frames = 0
    for data_block in output_data_dict.values():
        if isinstance(data_block, list):
            amount_of_frames = max([amount_of_frames, len(data_block)])

    # From WriterUtility.py
    if amount_of_frames != bpy.context.scene.frame_end - bpy.context.scene.frame_start:
        raise RuntimeError("The amount of images stored in the output_data_dict does not correspond with the amount"
                           "of images specified by frame_start to frame_end.")

    # Sorts out keys which are just metadata and not plottable
    keys_to_use = _GifWriterUtility.select_keys(output_data_dict)

    # Build temporary folders with .png collections
    to_animate = _GifWriterUtility.cache_png(keys_to_use, output_data_dict)

    # Write the cache .png files to .gif files and delete cache
    _GifWriterUtility.write_to_gif(to_animate, output_dir_path,
                                   append_to_existing_output,
                                   frame_duration_in_ms,
                                   reverse_animation)


class _GifWriterUtility:

    @staticmethod
    def provide_directory(output_dir_path: str) -> str:
        """ Generates subdirectory for .gif files if not existent """
        output_dir_path = os.path.join(output_dir_path, 'gif_animations')
        if not os.path.exists(output_dir_path):
            print(f"\n Generate output folder: {output_dir_path}")
            os.makedirs(output_dir_path)
        return output_dir_path

    @staticmethod
    def select_keys(output_data_dict: Dict[str, List[Union[np.ndarray, list, dict]]]) -> List[str]:
        """ Sorts out keys which are just metadata and not plottable """

        def is_image(x: Union[np.ndarray, list, dict]) -> bool:
            """ Checks if the input x is not a string and is not a vector """
            x = np.array(x)
            return not np.issubdtype(x.dtype, np.string_) and len(x.shape) != 1

        return [key for key, value in output_data_dict.items()
                if len(value) > 0 and is_image(value[0])]

    @staticmethod
    def cache_png(keys_to_use: List[str],
                  output_data_dict: Dict[str, List[Union[np.ndarray, list, dict]]]) -> Dict[str, List[str]]:
        """
        Builds temporary folders with .png collections
        and returns the locations as dictionary.
        """

        if not set(keys_to_use) <= set(output_data_dict.keys()):
            raise ValueError("The keys_to_use list must be contained in the list of keys from the output_data_dict!")

        to_animate = {}
        for key in keys_to_use:
            value = output_data_dict[key][0]
            value = np.array(value)
            # Check if frames are rendered in stereo vision
            if value.shape[0] == 2:
                # stereo images
                for index, perspective in enumerate(['_L', '_R']):
                    to_animate[key + perspective] = []
                    for number, frame in enumerate(output_data_dict[key]):
                        file_path = os.path.join(
                            Utility.get_temporary_directory(),
                            f'{number}_{key}_{perspective}.png')
                        to_animate[key + perspective].append(file_path)
                        vis_data(key=key,
                                 data=frame[index],
                                 save_to_file=file_path)
            else:
                # non stereo images
                to_animate[key] = []
                for number, frame in enumerate(output_data_dict[key]):
                    file_path = os.path.join(
                        Utility.get_temporary_directory(),
                        f'{number}_{key}.png')
                    to_animate[key].append(file_path)
                    vis_data(key=key,
                             data=frame,
                             save_to_file=file_path)
        return to_animate

    @staticmethod
    def look_for_existing_output(output_dir_path: str, append_to_existing_output: bool, name_ending: str) -> int:
        """
        Looks for the highest existing #.gif number and adapts respectively
        """
        if append_to_existing_output:
            gif_number = 0
            for path in os.listdir(output_dir_path):
                if path.endswith(name_ending):
                    index = path[:-len(name_ending)]
                    if index.isdigit():
                        gif_number = max(gif_number, int(index) + 1)
        else:
            gif_number = 0
        return gif_number

    @staticmethod
    def write_to_gif(to_animate: Dict[str, list],
                     output_dir_path: str,
                     append_to_existing_output: bool,
                     frame_duration_in_ms: int,
                     reverse_animation: bool) -> None:
        """
        Loads all .png files from each specific temporary folder and concatenates them to a single gif file respectively
        """
        for key, frame_list in to_animate.items():
            print(f'gif for {key}')
            if reverse_animation:
                frame_list.reverse()
            # loads actual picture data as frames
            frames = [Image.open(path) for path in frame_list]

            gif_number = _GifWriterUtility.look_for_existing_output(output_dir_path, append_to_existing_output,
                                                                    f"_{key}_animation.gif")
            file_name = f"{gif_number}_{key}_animation.gif"
            file = os.path.join(output_dir_path, file_name)
            frames[0].save(file, format='GIF', append_images=frames[1:], save_all=True, duration=frame_duration_in_ms,
                           loop=0)
