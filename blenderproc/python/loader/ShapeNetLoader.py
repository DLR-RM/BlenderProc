import glob
import json
import os
import pathlib
import random

import bpy

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.utility.Utility import resolve_path
from blenderproc.python.loader.ObjectLoader import load_obj


def load_shapenet(data_path: str, used_synset_id: str, used_source_id: str = "", move_object_origin: bool = True) -> MeshObject:
    """ This loads an object from ShapeNet based on the given synset_id, which specifies the category of objects to use.

    From these objects one is randomly sampled and loaded.

    Todo: not good:
    Note: if this module is used with another loader that loads objects with semantic mapping, make sure the other module is loaded first in the config file.

    :param data_path: The path to the ShapeNetCore.v2 folder.
    :param used_synset_id: The synset id for example: '02691156', check the data_path folder for more ids.
    :param used_source_id: Object identifier of the a particular ShapeNet category, see inside any ShapeNet category for identifiers
    :param move_object_origin: Moves the object center to the bottom of the bounding box in Z direction and also in the middle of the X and Y plane, this does not change the `.location` of the object. Default: True
    :return: The loaded mesh object.
    """
    data_path = resolve_path(data_path)
    taxonomy_file_path = os.path.join(data_path, "taxonomy.json")

    files_with_fitting_synset = ShapeNetLoader._get_files_with_synset(used_synset_id, used_source_id, taxonomy_file_path, data_path)
    selected_obj = random.choice(files_with_fitting_synset)
    loaded_objects = load_obj(selected_obj)

    # In shapenet every .obj file only contains one object, make sure that is the case
    if len(loaded_objects) != 1:
        raise Exception("The ShapeNetLoader expects every .obj file to contain exactly one object, however the file " + selected_obj + " contained " + str(len(loaded_objects)) + " objects.")
    obj = loaded_objects[0]

    obj.set_cp("used_synset_id", used_synset_id)
    obj.set_cp("used_source_id", pathlib.PurePath(selected_obj).parts[-3])

    ShapeNetLoader._correct_materials(obj)

    # removes the x axis rotation found in all ShapeNet objects, this is caused by importing .obj files
    # the object has the same pose as before, just that the rotation_euler is now [0, 0, 0]
    obj.persist_transformation_into_mesh(location=False, rotation=True, scale=False)

    # check if the move_to_world_origin flag is set
    if move_object_origin:
        # move the origin of the object to the world origin and on top of the X-Y plane
        # makes it easier to place them later on, this does not change the `.location`
        obj.move_origin_to_bottom_mean_point()
    bpy.ops.object.select_all(action='DESELECT')

    return obj

class ShapeNetLoader:

    @staticmethod
    def _get_files_with_synset(used_synset_id: str, used_source_id: str, path_to_taxonomy_file: str, data_path: str) -> list:
        """ Returns a list of a .obj file for the given synset_id

        :param used_synset_id: the id of the category something like: '02691156', see the data_path folder for more ids
        :param used_source_id: object identifier of the a particular ShapeNet category, see inside any ShapeNet category for identifiers
        :param path_to_taxonomy_file: path to the taxonomy.json file, should be in the data_path, too
        :param data_path: path to the ShapeNetCore.v2 folder
        :return: list of .obj files, which are in the synset_id folder, based on the given taxonomy
        """
        if os.path.exists(path_to_taxonomy_file):
            files = []
            with open(path_to_taxonomy_file, "r") as f:
                loaded_data = json.load(f)
                parent_synset_id = ShapeNetLoader.find_parent_synset_id(data_path, used_synset_id, loaded_data)
                id_path = os.path.join(data_path, parent_synset_id)

                if not used_source_id:
                    files.extend(glob.glob(os.path.join(id_path, "*", "models", "model_normalized.obj")))
                else:
                    if not os.path.exists(os.path.join(id_path, used_source_id)):
                        raise Exception("The used_source_id {} is not correct".format(used_source_id))

                    # Using both the used_synset_id and used_source_id
                    files.append(os.path.join(id_path, used_source_id, "models", "model_normalized.obj"))

            # Sort files to make random choice deterministic for the case when used_source_id is not specified
            files.sort()
            return files
        else:
            raise Exception("The taxonomy file could not be found: {}".format(path_to_taxonomy_file))

    @staticmethod
    def find_parent_synset_id(data_path, synset_id, json_data):
        """
        Returns the parent synset_id if it exists. If the synset_id is already parent synset_id, it is just returned
        :param data_path: path to the ShapeNetCore.v2 folder
        :param synset_id: the id of the category something like: '02691156', see the data_path folder for more ids
        :param json_data: loaded data from the ShapeNet taxonomy.json file
        :return: parent synset_id
        """
        id_path = os.path.join(data_path, synset_id)

        # Check if the synset_id is alreay a parent synset_id
        if os.path.exists(id_path):
            return synset_id

        for block in json_data:
            if synset_id in block["children"]:
                parent_synset_id = block["synsetId"]
                return ShapeNetLoader.find_parent_synset_id(data_path, parent_synset_id, json_data)

        raise Exception("The used_synset_id {} does not exists in the taxonomy file".format(synset_id))

    @staticmethod
    def _correct_materials(obj: MeshObject):
        """ If the used material contains an alpha texture, the alpha texture has to be flipped to be correct

        :param obj: object where the material maybe wrong
        """
        for material in obj.get_materials():
            if material is None:
                continue
            texture_nodes = material.get_nodes_with_type("ShaderNodeTexImage")
            if texture_nodes and len(texture_nodes) > 1:
                principled_bsdf = material.get_the_one_node_with_type("BsdfPrincipled")
                # find the image texture node which is connect to alpha
                node_connected_to_the_alpha = None
                for node_links in principled_bsdf.inputs["Alpha"].links:
                    if "ShaderNodeTexImage" in node_links.from_node.bl_idname:
                        node_connected_to_the_alpha = node_links.from_node
                # if a node was found which is connected to the alpha node, add an invert between the two
                if node_connected_to_the_alpha is not None:
                    invert_node = material.new_node("ShaderNodeInvert")
                    invert_node.inputs["Fac"].default_value = 1.0
                    material.insert_node_instead_existing_link(node_connected_to_the_alpha.outputs["Color"],
                                                              invert_node.inputs["Color"],
                                                              invert_node.outputs["Color"],
                                                              principled_bsdf.inputs["Alpha"])
