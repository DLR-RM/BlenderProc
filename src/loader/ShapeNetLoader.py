import glob
import json
import os
import random

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.LabelIdMapping import LabelIdMapping


class ShapeNetLoader(LoaderInterface):
    """
    This loads an object from ShapeNet based on the given synset_id, which specifies the category of objects to use.

    From these objects one is randomly sampled and loaded.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    Finally it sets all objects to have a category_id corresponding to the void class, 
    so it wouldn't trigger an exception in the SegMapRenderer.

    Note: if this module is used with another loader that loads objects with semantic mapping, make sure the other module is loaded first in the config file.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_path
          - The path to the ShapeNetCore.v2 folder.
          - string
        * - used_synset_id
          - The synset id for example: '02691156', check the data_path folder for more ids.
          - int
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

        self._data_path = Utility.resolve_path(self.config.get_string("data_path"))
        self._used_synset_id = self.config.get_string("used_synset_id")

        taxonomy_file_path = os.path.join(self._data_path, "taxonomy.json")
        self._files_with_fitting_synset = ShapeNetLoader.get_files_with_synset(self._used_synset_id, taxonomy_file_path,
                                                                               self._data_path)

    @staticmethod
    def get_files_with_synset(used_synset_id, path_to_taxonomy_file, data_path):
        """
        Returns a list of a .obj file for the given synset_id

        :param used_synset_id: the id of the category something like: '02691156', see the data_path folder for more ids
        :param path_to_taxonomy_file: path to the taxonomy.json file, should be in the data_path, too
        :param data_path: path to the ShapeNetCore.v2 folder
        :return: list of .obj files, which are in the synset_id folder, based on the given taxonomy
        """
        if os.path.exists(path_to_taxonomy_file):
            files = []
            with open(path_to_taxonomy_file, "r") as f:
                loaded_data = json.load(f)
                for block in loaded_data:
                    if "synsetId" in block:
                        synset_id = block["synsetId"]
                        if synset_id == used_synset_id or used_synset_id in block["children"]:
                            id_path = os.path.join(data_path, synset_id)
                            files.extend(glob.glob(os.path.join(id_path, "*", "models", "*.obj")))
            # Sort files to make random choice deterministic
            files.sort()
            return files
        else:
            raise Exception("The taxonomy file could not be found: {}".format(path_to_taxonomy_file))

    def run(self):
        """
        Uses the loaded .obj files and picks one randomly and loads it
        """
        selected_obj = random.choice(self._files_with_fitting_synset)
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
