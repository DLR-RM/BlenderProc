from typing import Dict, List, Union
from PIL import Image
import glob
import os
import tempfile

import bpy
import numpy as np
import matplotlib.pyplot as plt

try:
    from visHdf5Files import vis_data
except ModuleNotFoundError:
    from blenderproc.scripts.visHdf5Files import vis_data


def write_gif_animation(
        output_dir_path: str,
        output_data_dict: Dict[str, List[Union[np.ndarray, list, dict]]],
        append_to_existing_output: bool = True,
        time_constant: int = 50,
        time_direction: bool = False):
    """
    Generates a .gif file animation out of rendered frames

    :param output_dir_path: The directory path in which the gif 
                            animation folder will be saved
    :param output_data_dict: The data dictionary which was produced
                            by the render method.
    :param append_to_existing_output: If this is True, the output_dir_path
                            folder will be scanned for pre-existing
                            files of the name #_animation.gif 
                            and the number of newly added files will
                            start right where the last run left off.
    :param time_constant: Duration of each frame in the animation 
                            in milliseconds.
    :param time_direction: If this is True, the order of the frames
                            will be reversed.
    """

    # Generates subdirectory for .gif files
    output_dir_path = GifWriterUtility._provide_directory(output_dir_path)
    
    # From WriterUtility.py
    amount_of_frames = 0
    for data_block in output_data_dict.values():
        if isinstance(data_block, list):
            amount_of_frames = max([amount_of_frames, len(data_block)])

    # From WriterUtility.py
    if amount_of_frames != bpy.context.scene.frame_end - bpy.context.scene.frame_start:
        raise Exception("The amount of images stored in the output_data_dict"
                        "does not correspond with the amount"
                        "of images specified by frame_start to frame_end.")

    # Sorts out keys which are just metadata and not plottable
    keys_to_use = GifWriterUtility._select_keys(output_data_dict)

    # Build temporary folders with .png collections
    to_animate = GifWriterUtility._cache_png(keys_to_use, output_data_dict)

    # Write the cache .png files to .gif files and delete cache
    GifWriterUtility._write_to_gif(to_animate, output_dir_path, 
                                    append_to_existing_output, 
                                    time_constant, 
                                    time_direction)


class GifWriterUtility:
    
    @staticmethod
    def _provide_directory(output_dir_path: str) -> str:
        """ Generates subdirectory for .gif files if not existent """
        output_dir_path = os.path.join(output_dir_path, 'gif_animations')
        if not os.path.exists(output_dir_path):
            print('\n Generate output folder: ' + output_dir_path)
            os.makedirs(output_dir_path)
        return output_dir_path

    @staticmethod
    def _select_keys(
            output_data_dict: Dict[str, List[Union[np.ndarray, list, dict]]]
            ) -> List[str]:
        """ Sorts out keys which are just metadata and not plottable """
        keys_to_use = []
        for key in output_data_dict.keys():
            value = output_data_dict[key][0]
            value = np.array(value)
            if np.issubdtype(value.dtype, np.string_) or len(value.shape) == 1:
                pass # metadata
            else:
                keys_to_use.append(key)
        return keys_to_use

    @staticmethod
    def _cache_png(keys_to_use: List[str], 
            output_data_dict: Dict[str, List[Union[np.ndarray, list, dict]]]
            ) -> Dict[str, str]:
        """
        Builds temporary folders with .png collections 
        and returns the locations as dictionary. 
        """

        if not set(keys_to_use) <= set(output_data_dict.keys()):
            raise ValueError("The keys_to_use list must be contained in"
                            "the list of keys from the output_data_dict!")

        to_animate = dict()
        for key in keys_to_use:
            value = output_data_dict[key][0]
            value = np.array(value)
            # Check if frames are rendered in stereo vision
            if value.shape[0] is 2:
                # stereo images
                for index, perspective in enumerate(['_L', '_R']):
                    tmp_dir = tempfile.TemporaryDirectory()
                    print('Temporary directory for ' 
                            + key 
                            + perspective 
                            + ': ' 
                            + tmp_dir.name)
                    to_animate.update({key + perspective: tmp_dir})
                    for number, frame in enumerate(output_data_dict[key]):
                        vis_data(key=key,
                                data=frame[index], 
                                save_to_file=tmp_dir.name + f'/{number}.png')
            else:
                # non stereo images
                tmp_dir = tempfile.TemporaryDirectory()
                print('Temporary directory for ' + key + ': ' + tmp_dir.name)
                to_animate.update({key: tmp_dir})
                for number, frame in enumerate(output_data_dict[key]):
                    vis_data(key=key, 
                            data=frame, 
                            save_to_file=tmp_dir.name + f'/{number}.png')
        return to_animate

    @staticmethod
    def _sort_method(item) -> int:
        """ Order the images due to the file numbering """
        _, file_name = item.rsplit('/', maxsplit=1)
        file_number, _ = file_name.split('.')
        return int(file_number)

    @staticmethod
    def _look_for_existing_output(output_dir_path: str, 
                                append_to_existing_output: bool, 
                                name_ending: str) -> int:
        """ 
        Looks for the highest existing #.gif number 
        and adapts respectivly 
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
    def _write_to_gif(to_animate: Dict[str, str], 
                    output_dir_path: str, 
                    append_to_existing_output: bool, 
                    time_constant: int, 
                    time_direction: bool) -> None:
        """
        loads all .png files from each specific temporary folder 
        and concatenates them to a single gif file respectively 
        """
        for key, tmp_dir in to_animate.items():
            print('gif for ' + key + ' at ' + tmp_dir.name)
            frames = []
            # Loads all .png images as paths to a list
            frame_paths = glob.glob(tmp_dir.name + '/*.png')
            # sorts list in size w.r.t. given key
            frame_paths.sort(key = GifWriterUtility._sort_method, 
                            reverse=time_direction)
            
            # loads actual picture data as frames
            for frame_path in frame_paths:
                new_frame = Image.open(frame_path)
                frames.append(new_frame)

            name_ending = f"_{key}_animation.gif"
            gif_number = GifWriterUtility._look_for_existing_output(
                                            output_dir_path, 
                                            append_to_existing_output, 
                                            name_ending)
            file_name = str(gif_number) + name_ending
            file = os.path.join(output_dir_path, file_name)
            frames[0].save(file,
                            format ='GIF',
                            append_images = frames[1:],
                            save_all = True,
                            duration = time_constant,
                            loop = 0)
            GifWriterUtility._delete_temp_dir(tmp_dir, key)

    @staticmethod
    def _delete_temp_dir(tmp_dir: str, key: str) -> None:
        """
        Deletes the temporary directory where the .png files
        were stored 
        """
        tmp_dir.cleanup()
        print('Deleted temporary' + key + ' directory: '+ tmp_dir.name)