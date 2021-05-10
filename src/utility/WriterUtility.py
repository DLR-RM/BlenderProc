import os
import numpy as np
import csv
import math
import json

import bpy
import mathutils

from src.utility.BlenderUtility import load_image
from src.utility.MathUtility import MathUtility
from src.utility.Utility import Utility
from src.utility.CameraUtility import CameraUtility


class WriterUtility:
    
    @staticmethod
    def load_registered_outputs(keys: list):
        """
        Loads registered outputs with specified keys

        param keys: list of output_key types to load
        :return: dict of lists of raw loaded outputs. Keys can be 'distance', 'colors', 'normals'
        """
        output_data_dict = {}
        reg_outputs = Utility.get_registered_outputs()

        for reg_out in reg_outputs:
            if reg_out['key'] in keys:
                output_data_dict[reg_out['key']] = []
                for frame_id in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
                    output_path = Utility.resolve_path(reg_out['path'] % frame_id)
                    output_file = WriterUtility.load_output_file(output_path)
                    output_data_dict[reg_out['key']].append(output_file)

        return output_data_dict
    
    @staticmethod
    def load_output_file(file_path:str, write_alpha_channel:bool=False):
        """ Tries to read in the file with the given path into a numpy array.

        :param file_path: The file path. Type: string.
        :param write_alpha_channel: Whether to load the alpha channel as well. Type: bool. Default: False
        :return: A numpy array containing the data of the file.
        """
        if not os.path.exists(file_path):
            raise Exception("File not found: " + file_path)

        file_ending = file_path[file_path.rfind(".") + 1:].lower()

        if file_ending in ["exr", "png", "jpg"]:
            #num_channels is 4 if transparent_background is true in config
            return load_image(file_path, num_channels = 3 + write_alpha_channel)
        elif file_ending in ["npy", "npz"]:
            return np.load(file_path)
        elif file_ending in ["csv"]:
            return WriterUtility._load_csv(file_path)
        else:
            raise NotImplementedError("File with ending " + file_ending + " cannot be loaded.")
    
    @staticmethod
    def _load_csv(file_path:str):
        """ Load the csv file at the given path.

        :param file_path: The path. Type: string.
        :return: The content of the file
        """
        rows = []
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                rows.append(row)
        return np.string_(json.dumps(rows))  # make the list of dicts as a string
    
    @staticmethod
    def get_common_attribute(item, attribute_name:str, destination_frame:str=["X", "Y", "Z"]):
        """ Returns the value of the requested attribute for the given item.

        This method covers all general attributes that blender objects have.

        :param item: The item. Type: blender object.
        :param attribute_name: The attribute name. Type: string.
        :param destination_frame: Used to transform item to blender coordinates. Default: ["X", "Y", "Z"]
        :return: The attribute value.
        """    
            
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
    def get_cam_attribute(cam_ob:bpy.context.scene.camera, attribute_name:str, destination_frame:str=["X", "Y", "Z"]):
        """ Returns the value of the requested attribute for the given object.

        :param cam_ob: The camera object.
        :param attribute_name: The attribute name. Type: string.
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
        elif attribute_name == "cam2world_matrix":
            return WriterUtility.get_common_attribute(cam_ob, "matrix_world", destination_frame)
        else:
            return WriterUtility.get_common_attribute(cam_ob, attribute_name, destination_frame)
    
    @staticmethod    
    def get_light_attribute(light, attribute_name):
        """ Returns the value of the requested attribute for the given light.

        :param light: The light. Type: blender scene object of type light.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """
        if attribute_name == "energy":
            return light.data.energy
        else:
            return WriterUtility.get_common_attribute(light, attribute_name)
    
    @staticmethod    
    def _get_shapenet_attribute(shapenet_obj, attribute_name):
        """ Returns the value of the requested attribute for the given object.
        :param shapenet_obj: The ShapeNet object.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """

        if attribute_name == "used_synset_id":
            return shapenet_obj.get("used_synset_id", "")
        elif attribute_name == "used_source_id":
            return shapenet_obj.get("used_source_id", "")
        else:
            return WriterUtility.get_common_attribute(shapenet_obj, attribute_name)
