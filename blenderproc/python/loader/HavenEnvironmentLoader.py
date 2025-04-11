"""Load the haven environmental data to set it as an HDRi background."""

import glob
import os
import random
from typing import Union

import numpy as np
from mathutils import Euler

import bpy

from blenderproc.python.utility.Utility import Utility


def set_world_background_hdr_img(path_to_hdr_file: str, strength: float = 1.0,
                                 rotation_euler: Union[list, Euler, np.ndarray] = None):
    """
    Sets the world background to the given hdr_file.

    :param path_to_hdr_file: Path to the .hdr file
    :param strength: The brightness of the background.
    :param rotation_euler: The euler angles of the background.
    """
    if rotation_euler is None:
        rotation_euler = [0.0, 0.0, 0.0]

    if not os.path.exists(path_to_hdr_file):
        raise FileNotFoundError(f"The given path does not exists: {path_to_hdr_file}")

    world = bpy.context.scene.world
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # add a texture node and load the image and link it
    texture_node = nodes.new(type="ShaderNodeTexEnvironment")
    texture_node.image = bpy.data.images.load(path_to_hdr_file, check_existing=True)

    # get the one background node of the world shader
    background_node = Utility.get_the_one_node_with_type(nodes, "Background")

    # link the new texture node to the background
    links.new(texture_node.outputs["Color"], background_node.inputs["Color"])

    # Set the brightness of the background
    background_node.inputs["Strength"].default_value = strength

    # add a mapping node and a texture coordinate node
    mapping_node = nodes.new("ShaderNodeMapping")
    tex_coords_node = nodes.new("ShaderNodeTexCoord")

    #link the texture coordinate node to mapping node
    links.new(tex_coords_node.outputs["Generated"], mapping_node.inputs["Vector"])

    #link the mapping node to the texture node
    links.new(mapping_node.outputs["Vector"], texture_node.inputs["Vector"])

    mapping_node.inputs["Rotation"].default_value = rotation_euler

def get_random_world_background_hdr_img_path_from_haven(data_path: str) -> str:
    """ Sets the world background to a random .hdr file from the given directory.

    :param data_path: A path pointing to a directory containing .hdr files.
    :return: The path to a random selected path
    """

    if os.path.exists(data_path):
        data_path = os.path.join(data_path, "hdris")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"The folder: {data_path} does not contain a folder name hdfris. "
                                    f"Please use the download script.")
    else:
        raise FileNotFoundError(f"The data path does not exists: {data_path}")

    hdr_files = glob.glob(os.path.join(data_path, "*", "*.hdr"))
    # this will be ensure that the call is deterministic
    hdr_files.sort()

    # this file be used
    random_hdr_file = random.choice(hdr_files)

    return random_hdr_file
