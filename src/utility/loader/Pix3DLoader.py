import json
import os
import random
from typing import List

import bpy

from src.utility.LabelIdMapping import LabelIdMapping
from src.utility.MeshObjectUtility import MeshObject
from src.utility.Utility import Utility
from src.utility.loader.ObjectLoader import ObjectLoader


class Pix3DLoader:
    """
    This loads an object from Pix3D based on the given category of objects to use.

    From these objects one is randomly sampled and loaded.

    Finally it sets all objects to have a category_id corresponding to the void class,
    so it wouldn't trigger an exception in the SegMapRenderer.

    Note: if this class is used with another loader that loads objects with semantic mapping, make sure the other
    module is loaded first. TODO: Really?
    """

    @staticmethod
    def get_files_with_category(used_category: str, data_path: str) -> list:
        """
        Returns a list of a .obj file for the given category. This function creates a category path file for each used
        category. This will speed up the usage the next time the category is used.

        :param used_category: the category something like: 'bed', see the data_path folder for categories
        :param data_path: path to the Pix3D folder
        :return: list of .obj files, which are in the data_path folder, based on the given category
        """

        path_to_annotation_file = os.path.join(data_path, "pix3d.json")
        if os.path.exists(path_to_annotation_file):
            files = []
            path_to_category_file = os.path.join(data_path, "category_{}_paths.txt".format(used_category.strip()))
            if os.path.exists(path_to_category_file):
                with open(path_to_category_file, "r") as f:
                    files = f.read().split("\n")
            else:
                with open(path_to_annotation_file, "r") as f:
                    loaded_data = json.load(f)
                    for block in loaded_data:
                        if "category" in block:
                            category = block["category"]
                            if category == used_category:
                                files.append(block["model"])
                # remove doubles
                files = list(set(files))
                with open(path_to_category_file, "w") as f:
                    f.write("\n".join(files))
            files = [os.path.join(data_path, file) for file in files]
            return files
        else:
            raise Exception("The annotation file could not be found: {}".format(path_to_annotation_file))

    @staticmethod
    def load(used_category: str, data_path: str = 'resources/pix3d') -> List[MeshObject]:
        """ Loads one random Pix3D object from the given category.

        :param used_category: The category to use for example: 'bed', check the data_path/model folder for more categories.
                              Available: ['bed', 'bookcase', 'chair', 'desk', 'misc', 'sofa', 'table', 'tool', 'wardrobe']
        :param data_path: The path to the Pix3D folder.
        :return: The list of loaded mesh objects.
        """
        data_path = Utility.resolve_path(data_path)
        files_with_fitting_category = Pix3DLoader.get_files_with_category(used_category, data_path)

        selected_obj = random.choice(files_with_fitting_category)
        loaded_obj = ObjectLoader.load(selected_obj)

        Pix3DLoader._correct_materials(loaded_obj)

        if "void" in LabelIdMapping.label_id_map:  # Check if using an id map
            for obj in loaded_obj:
                obj.set_cp('category_id', LabelIdMapping.label_id_map["void"])

        # removes the x axis rotation found in all ShapeNet objects, this is caused by importing .obj files
        # the object has the same pose as before, just that the rotation_euler is now [0, 0, 0]
        for obj in loaded_obj:
            obj.remove_x_axis_rotation()

        # move the origin of the object to the world origin and on top of the X-Y plane
        # makes it easier to place them later on, this does not change the `.location`
        for obj in loaded_obj:
            obj.move_origin_to_bottom_mean_point()
        bpy.ops.object.select_all(action='DESELECT')

        return loaded_obj

    @staticmethod
    def _correct_materials(objects: List[MeshObject]):
        """ If the used material contains an alpha texture, the alpha texture has to be flipped to be correct

        :param objects: The list of mesh objects where the material maybe wrong.
        """

        for obj in objects:
            for material in obj.get_materials():
                nodes = material.node_tree.nodes
                links = material.node_tree.links
                texture_nodes = Utility.get_nodes_with_type(nodes, "ShaderNodeTexImage")
                if texture_nodes and len(texture_nodes) > 1:
                    principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                    # find the image texture node which is connect to alpha
                    node_connected_to_the_alpha = None
                    for node_links in principled_bsdf.inputs["Alpha"].links:
                        if "ShaderNodeTexImage" in node_links.from_node.bl_idname:
                            node_connected_to_the_alpha = node_links.from_node
                    # if a node was found which is connected to the alpha node, add an invert between the two
                    if node_connected_to_the_alpha is not None:
                        invert_node = nodes.new("ShaderNodeInvert")
                        invert_node.inputs["Fac"].default_value = 1.0
                        Utility.insert_node_instead_existing_link(links, node_connected_to_the_alpha.outputs["Color"],
                                                                  invert_node.inputs["Color"],
                                                                  invert_node.outputs["Color"],
                                                                  principled_bsdf.inputs["Alpha"])
