import os
from typing import List, Dict, Union, Any, Set, Tuple

from src.utility.SetupUtility import SetupUtility
SetupUtility.setup_pip(["h5py"])

import numpy as np
import csv
import json

import bpy
import mathutils
import h5py

from src.utility.BlenderUtility import load_image
from src.utility.MathUtility import MathUtility
from src.utility.Utility import Utility
from src.utility.CameraUtility import CameraUtility


class WriterUtility:

    @staticmethod
    def load_registered_outputs(keys: Set[str]) -> Dict[str, List[np.ndarray]]:
        """
        Loads registered outputs with specified keys

        :param keys: set of output_key types to load
        :return: dict of lists of raw loaded outputs. Keys are e.g. 'distance', 'colors', 'normals', 'segmap'
        """
        output_data_dict = {}
        reg_outputs = Utility.get_registered_outputs()
        for reg_out in reg_outputs:
            if reg_out['key'] in keys:
                if '%' in reg_out['path']:
                    # per frame outputs
                    for frame_id in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
                        output_path = Utility.resolve_path(reg_out['path'] % frame_id)
                        if os.path.exists(output_path):
                            output_file = WriterUtility.load_output_file(output_path)
                        else:
                            try:
                                # check for stereo files
                                output_paths = WriterUtility._get_stereo_path_pair(output_path)
                                # convert to a tensor of shape [2, img_x, img_y, channels]
                                # output_file[0] is the left image and output_file[1] the right image
                                output_file = np.array([WriterUtility.load_output_file(path) for path in output_paths])
                            except:
                                raise('Could not find original or stereo paths: {}'.format(output_paths))
                        output_data_dict.setdefault(reg_out['key'], []).append(output_file)
                else:
                    # per run outputs
                    output_path = Utility.resolve_path(reg_out['path'])
                    output_file = WriterUtility.load_output_file(output_path)
                    output_data_dict[reg_out['key']] = output_file

        return output_data_dict
    
    @staticmethod
    def _get_stereo_path_pair(file_path: str) -> Tuple[str, str]:
        """
        Returns stereoscopic file path pair for a given "normal" image file path.

        :param file_path: The file path of a single image.
        :return: The pair of file paths corresponding to the stereo images,
        """
        path_split = file_path.split(".")
        path_l = "{}_L.{}".format(path_split[0], path_split[1])
        path_r = "{}_R.{}".format(path_split[0], path_split[1])

        return path_l, path_r

    @staticmethod
    def load_output_file(file_path: str, write_alpha_channel: bool = False, remove: bool = True) -> np.ndarray:
        """ Tries to read in the file with the given path into a numpy array.

        :param file_path: The file path. Type: string.
        :param write_alpha_channel: Whether to load the alpha channel as well. Type: bool. Default: False
        :param remove: Whether to delete file after loading.
        :return: Loaded data from the file as numpy array if possible.
        """
        if not os.path.exists(file_path):
            raise Exception("File not found: " + file_path)

        file_ending = file_path[file_path.rfind(".") + 1:].lower()

        if file_ending in ["exr", "png", "jpg"]:
            # num_channels is 4 if transparent_background is true in config
            output = load_image(file_path, num_channels=3 + (1 if write_alpha_channel else 0))
        elif file_ending in ["npy", "npz"]:
            output =  np.load(file_path)
        elif file_ending in ["csv"]:
            output =  WriterUtility._load_csv(file_path)
        else:
            raise NotImplementedError("File with ending " + file_ending + " cannot be loaded.")

        if remove:
            os.remove(file_path)        
        return output

    @staticmethod
    def _load_csv(file_path: str) -> np.ndarray:
        """ Load the csv file at the given path.

        :param file_path: The path. Type: string.
        :return: The content of the file
        """
        rows = []
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                rows.append(row)
        return rows

    @staticmethod
    def get_common_attribute(item: bpy.types.Object, attribute_name: str,
                             destination_frame: Union[None, List[str]] = None) -> Any:
        """ Returns the value of the requested attribute for the given item.

        This method covers all general attributes that blender objects have.

        :param item: The item. Type: blender object.
        :param attribute_name: The attribute name. Type: string.
        :param destination_frame: Used to transform item to blender coordinates. Default: ["X", "Y", "Z"]
        :return: The attribute value.
        """

        if destination_frame is None:
            destination_frame = ["X", "Y", "Z"]

        if attribute_name == "name":
            return item.name
        elif attribute_name == "location":
            return MathUtility.transform_point_to_blender_coord_frame(item.location, destination_frame)
        elif attribute_name == "rotation_euler":
            return MathUtility.transform_point_to_blender_coord_frame(item.rotation_euler, destination_frame)
        elif attribute_name == "rotation_forward_vec":
            # Calc forward vector from rotation matrix
            rot_mat = item.rotation_euler.to_matrix()
            forward = rot_mat @ mathutils.Vector([0, 0, -1])
            return MathUtility.transform_point_to_blender_coord_frame(forward, destination_frame)
        elif attribute_name == "rotation_up_vec":
            # Calc up vector from rotation matrix
            rot_mat = item.rotation_euler.to_matrix()
            up = rot_mat @ mathutils.Vector([0, 1, 0])
            return MathUtility.transform_point_to_blender_coord_frame(up, destination_frame)
        elif attribute_name == "matrix_world":
            # Transform matrix_world to given destination frame
            matrix_world = Utility.transform_matrix_to_blender_coord_frame(item.matrix_world, destination_frame)
            return [[x for x in c] for c in matrix_world]
        elif attribute_name.startswith("customprop_"):
            custom_property_name = attribute_name[len("customprop_"):]
            # Make sure the requested custom property exist
            if custom_property_name in item:
                return item[custom_property_name]
            else:
                raise Exception("No such custom property: " + custom_property_name)
        else:
            raise Exception("No such attribute: " + attribute_name)

    @staticmethod
    def get_cam_attribute(cam_ob: bpy.context.scene.camera, attribute_name: str,
                          destination_frame: Union[List[str], None] = None) -> Any:
        """ Returns the value of the requested attribute for the given object.

        :param cam_ob: The camera object.
        :param attribute_name: The attribute name.
        :param destination_frame: Used to transform camera to blender coordinates. Default: ["X", "Y", "Z"]
        :return: The attribute value.
        """

        if attribute_name == "fov_x":
            return cam_ob.data.angle_x
        elif attribute_name == "fov_y":
            return cam_ob.data.angle_y
        elif attribute_name == "shift_x":
            return cam_ob.data.shift_x
        elif attribute_name == "shift_y":
            return cam_ob.data.shift_y
        elif attribute_name == "half_fov_x":
            return cam_ob.data.angle_x * 0.5
        elif attribute_name == "half_fov_y":
            return cam_ob.data.angle_y * 0.5
        elif attribute_name == "cam_K":
            return [[x for x in c] for c in CameraUtility.get_intrinsics_as_K_matrix()]
        else:
            if destination_frame is None:
                destination_frame = ["X", "Y", "Z"]
            if attribute_name == "cam2world_matrix":
                return WriterUtility.get_common_attribute(cam_ob, "matrix_world", destination_frame)
            else:
                return WriterUtility.get_common_attribute(cam_ob, attribute_name, destination_frame)

    @staticmethod
    def get_light_attribute(light: bpy.types.Light, attribute_name: str) -> Any:
        """ Returns the value of the requested attribute for the given light.

        :param light: The light. Type: blender scene object of type light.
        :param attribute_name: The attribute name.
        :return: The attribute value.
        """
        if attribute_name == "energy":
            return light.data.energy
        else:
            return WriterUtility.get_common_attribute(light, attribute_name)

    @staticmethod
    def _get_shapenet_attribute(shapenet_obj: bpy.types.Object, attribute_name: str):
        """ Returns the value of the requested attribute for the given object.

        :param shapenet_obj: The ShapeNet object.
        :param attribute_name: The attribute name.
        :return: The attribute value.
        """

        if attribute_name == "used_synset_id":
            return shapenet_obj.get("used_synset_id", "")
        elif attribute_name == "used_source_id":
            return shapenet_obj.get("used_source_id", "")
        else:
            return WriterUtility.get_common_attribute(shapenet_obj, attribute_name)

    @staticmethod
    def save_to_hdf5(output_dir_path: str, output_data_dict: Dict[str, List[np.ndarray]],
                     append_to_existing_output: bool = False, stereo_separate_keys: bool = False):
        """
        Saves the information provided inside of the output_data_dict into a .hdf5 container

        :param output_dir_path: The folder path in which the .hdf5 containers will be generated
        :param output_data_dict: The container, which keeps the different images, which should be saved to disc.
                                 Each key will be saved as its own key in the .hdf5 container.
        :param append_to_existing_output: If this is True, the output_dir_path folder will be scanned for pre-existing
                                          .hdf5 containers and the numbering of the newly added containers, will start
                                          right where the last run left off.
        :param stereo_separate_keys: If this is True and the rendering was done in stereo mode, than the stereo images
                                     won't be saved in one tensor [2, img_x, img_y, channels], where the img[0] is the
                                     left image and img[1] the right. They will be saved in separate keys: for example
                                     for colors in colors_0 and colors_1.
        """

        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)

        amount_of_frames = 0
        for data_block in output_data_dict.values():
            if isinstance(data_block, list):
                amount_of_frames = max([amount_of_frames, len(data_block)])

        # if append to existing output is turned on the existing folder is searched for the highest occurring
        # index, which is then used as starting point for this run
        if append_to_existing_output:
            frame_offset = 0
            # Look for hdf5 file with highest index
            for path in os.listdir(output_dir_path):
                if path.endswith(".hdf5"):
                    index = path[:-len(".hdf5")]
                    if index.isdigit():
                        frame_offset = max(frame_offset, int(index) + 1)
        else:
            frame_offset = 0

        if amount_of_frames != bpy.context.scene.frame_end - bpy.context.scene.frame_start:
            raise Exception("The amount of images stored in the output_data_dict does not correspond with the amount"
                            "of images specified by frame_start to frame_end.")

        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            # for each frame a new .hdf5 file is generated
            hdf5_path = os.path.join(output_dir_path, str(frame + frame_offset) + ".hdf5")
            with h5py.File(hdf5_path, "w") as file:
                # Go through all the output types
                print(f"Merging data for frame {frame} into {hdf5_path}")

                for key, data_block in output_data_dict.items():
                    if frame < len(data_block):
                        # get the current data block for the current frame
                        used_data_block = data_block[frame]
                        if stereo_separate_keys and (bpy.context.scene.render.use_multiview or
                                                     used_data_block.shape[0] == 2):
                            # stereo mode was activated
                            WriterUtility._write_to_hdf_file(file, key + "_0", data_block[frame][0])
                            WriterUtility._write_to_hdf_file(file, key + "_1", data_block[frame][1])
                        else:
                            WriterUtility._write_to_hdf_file(file, key, data_block[frame])
                    else:
                        raise Exception(f"There are more frames {frame} then there are blocks of information "
                                        f" {len(data_block)} in the given list for key {key}.")
                blender_proc_version = Utility.get_current_version()
                if blender_proc_version:
                    WriterUtility._write_to_hdf_file(file, "blender_proc_version", np.string_(blender_proc_version))

    @staticmethod
    def _write_to_hdf_file(file, key: str, data: np.ndarray, compression: str = "gzip"):
        """ Adds the given data as a new entry to the given hdf5 file.

        :param file: The hdf5 file handle. Type: hdf5.File
        :param key: The key at which the data should be stored in the hdf5 file.
        :param data: The data to store.
        """
        if not isinstance(data, np.ndarray) and not isinstance(data, np.bytes_):
            if isinstance(data, list):
                if len(data)>0 and isinstance(data[0], dict):
                    data = np.string_(json.dumps(data))
                data = np.array(data)
            else:
                raise Exception(f"This fct. expects the data for key {key} to be a np.ndarray not a {type(data)}!")

        if data.dtype.char == 'S':
            file.create_dataset(key, data=data, dtype=data.dtype)
        else:
            file.create_dataset(key, data=data, compression=compression)
