import glob
import os
import random

import bpy

from src.utility.Utility import Utility


class HavenEnvironmentLoader:
    """ This class can load hdr images as background images, which will replace the default grey background. """

    @staticmethod
    def set_random_world_background_hdr_img(data_path: str):
        """ Sets the world background to a random .hdr file from the given directory.

        :param data_path: A path pointing to a directory containing .hdr files.
        """

        if os.path.exists(data_path):
            data_path = os.path.join(data_path, "hdris")
            if not os.path.exists(data_path):
                raise Exception("The folder: {} does not contain a folder name hdfris. Please use the "
                                "download script.".format(data_path))
        else:
            raise Exception("The data path does not exists: {}".format(data_path))

        hdr_files = glob.glob(os.path.join(data_path, "*", "*.hdr"))
        # this will be ensure that the call is deterministic
        hdr_files.sort()

        # this file be used
        random_hdr_file = random.choice(hdr_files)

        # set the world background with the chosen random_hdr_file
        HavenEnvironmentLoader.set_world_background_hdr_img(random_hdr_file)

    @staticmethod
    def set_world_background_hdr_img(path_to_hdr_file):
        """
        Sets the world background to the given hdr_file.

        :param path_to_hdr_file: Path to the .hdr file
        """

        if not os.path.exists(path_to_hdr_file):
            raise Exception("The given path does not exists: {}".format(path_to_hdr_file))

        world = bpy.context.scene.world
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # add a texture node and load the image and link it
        texture_node = nodes.new(type="ShaderNodeTexEnvironment")
        texture_node.image = bpy.data.images.load(path_to_hdr_file, check_existing=True)

        # get the one output node of the world shader
        output_node = Utility.get_the_one_node_with_type(nodes, "Output")

        # link the new texture node to the output
        links.new(texture_node.outputs["Color"], output_node.inputs["Surface"])
