import json
import os
import random

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.LabelIdMapping import LabelIdMapping


class Pix3DLoader(LoaderInterface):
    """
    This loads an object from Pix3D based on the given category of objects to use.

    From these objects one is randomly sampled and loaded.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    Finally it sets all objects to have a category_id corresponding to the void class, 
    so it wouldn't trigger an exception in the SegMapRenderer.

    Note: if this module is used with another loader that loads objects with semantic mapping, make sure the other
    module is loaded first in the config file.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_path
          - The path to the Pix3D folder. Default: 'resources/pix3d'.
          - string
        * - category
          - The category to use for example: 'bed', check the data_path/model folder for more categories. Available:
            ['bed', 'bookcase', 'chair', 'desk', 'misc', 'sofa', 'table', 'tool'" , 'wardrobe']
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

        self._data_path = Utility.resolve_path(self.config.get_string("data_path", "resources/pix3d"))
        self._used_category = self.config.get_string("used_category")

        self._files_with_fitting_category = Pix3DLoader.get_files_with_category(self._used_category, self._data_path)

    @staticmethod
    def get_files_with_category(used_category, data_path):
        """
        Returns a list of a .obj file for the given category. This function creates a category path file for each used
        category. This will speed up the usage the next time the category is used.

        :param category: the category something like: 'bed', see the data_path folder for categories
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

    def run(self):
        """
        Uses the loaded .obj files and picks one randomly and loads it
        """
        selected_obj = random.choice(self._files_with_fitting_category)
        loaded_obj = Utility.import_objects(selected_obj)

        self._correct_materials(loaded_obj)

        self._set_properties(loaded_obj)

        if "void" in LabelIdMapping.label_id_map:  # Check if using an id map
            for obj in loaded_obj:
                obj['category_id'] = LabelIdMapping.label_id_map["void"]

        # removes the x axis rotation found in all ShapeNet objects, this is caused by importing .obj files
        # the object has the same pose as before, just that the rotation_euler is now [0, 0, 0]
        LoaderInterface.remove_x_axis_rotation(loaded_obj)

        # move the origin of the object to the world origin and on top of the X-Y plane
        # makes it easier to place them later on, this does not change the `.location`
        LoaderInterface.move_obj_origin_to_bottom_mean_point(loaded_obj)
        bpy.ops.object.select_all(action='DESELECT')

    def _correct_materials(self, objects):
        """
        If the used material contains an alpha texture, the alpha texture has to be flipped to be correct

        :param objects: objects where the material maybe wrong
        """

        for obj in objects:
            for mat_slot in obj.material_slots:
                material = mat_slot.material
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
