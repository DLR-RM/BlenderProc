import glob
import os
import random
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Tuple

import addon_utils
import bpy

from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.utility.Utility import resolve_path
from blenderproc.python.material import MaterialLoaderUtility
from blenderproc.python.utility.Utility import Utility

"""Haven textures are stored as a directory with several texture maps .jpgs e.g:
textures
|- rock_01
|  |- rock_01_ao_1k.jpg
|  |- rock_01_diff_1k.jpg
|  |- rock_01_disp_1k.jpg
|  |- rock_01_nor_gl_1k.jpg
|  |- rock_01_rough_1k.jpg
|- rock_02
| ...

The general naming pattern of the texture maps is: {name}_{type}_{resolution}.jpg
However, the type abbreviation is not consistent for all textures. E.g. for some textures the base color map is 
identified with "diff" and for other with "col". The texture_map_identifiers dictionary tracks these variations.
"""
texture_map_identifiers = {
    "base color": ["diff", "diffuse", "col", "albedo"],
    "ambient occlusion": ["ao"],
    "specular": ["spec"],
    "roughness": ["rough"],
    "normal": ["nor", "nor_gl"],
    "displacement": ["disp", "displacement", "height"],
    "bump": ["bump"],
    "transparency": ["alpha"]
}


def identify_base_color_image_path(texture_map_paths: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """Finds the path to the base color image in a list of texture map paths.
    We do this by looking for any of the "base color" identifiers in each path.
    We also make sure to account for different capitalizations of the identifier.

    :param texture_map_paths: paths to check
    :type texture_map_paths: list of strings
    :return: path to the base color image and the specific identifier
    :rtype: tuple of 2 strings
    """
    for texture_map_path in texture_map_paths:
        for identifier_lowercase in texture_map_identifiers["base color"]:
            search_string = f"_{identifier_lowercase}_"
            search_start = texture_map_path.lower().find(search_string)
            if search_start != -1:
                identifier_start = search_start + 1
                identifier_end = identifier_start+len(identifier_lowercase)
                identifier = texture_map_path[identifier_start:identifier_end]
                return texture_map_path, identifier
    return None, None


def identify_texture_maps(texture_folder_path: Union[str, Path]) -> Optional[Dict[str, str]]:
    """Finds the paths of the different textures maps in a texture folder.

    :param texture_folder_path: path to the texture folder
    :return: dictionary that maps texture map types to their path when found, else it maps to an empty string
    """
    if isinstance(texture_folder_path, str):
        texture_folder_path = Path(texture_folder_path)
    texture_map_paths = [str(path.absolute()) for path in texture_folder_path.glob("*.jpg")]
    color_path, color_identifier = identify_base_color_image_path(texture_map_paths)

    if not color_path:
        return None

    texture_map_types = texture_map_identifiers.keys()
    texture_map_paths_by_type = {type: "" for type in texture_map_types}
    texture_map_paths_by_type["base color"] = color_path

    # To find the other texture maps, we replace the color identifier, with the identifiers of the other texture map
    # types. By comparing lowercase paths, we also account for different capitalizations e.g. Nor, NOR, NoR, ...
    for type in texture_map_types:
        for identifier in texture_map_identifiers[type]:
            texture_map_path_lowercase = color_path.replace(color_identifier, identifier).lower()   
            for path in texture_map_paths:
                if path.lower() == texture_map_path_lowercase:
                    texture_map_paths_by_type[type] = path
                    break

    return texture_map_paths_by_type


def load_haven_mat(folder_path: Union[str, Path] = "resources/haven", used_assets: Optional[List[str]] = None,
                   preload: bool = False, fill_used_empty_materials: bool = False,
                   add_cp: Optional[Dict[str, Any]] = None, return_random_element: bool = False) \
        -> Union[List[Material], Material]:
    """ Loads all specified haven textures from the given directory.

    :param folder_path: The path to the downloaded haven.
    :param used_assets: A list of all asset names, you want to use. The asset-name must not be typed in completely,
                        only the beginning the name starts with. By default all assets will be loaded, specified
                        by an empty list or None.
    :param preload: If set true, only the material names are loaded and not the complete material.
    :param fill_used_empty_materials: If set true, the preloaded materials, which are used are now loaded completely.
    :param add_cp: A dictionary of materials and the respective properties.
    :param return_random_element: If this is True only a single Material is loaded and returned, if you want to sample
                                  many materials load them all with the preload option, use them and then fill the used
                                  empty materials instead of calling this function multiple times.
    :return a list of all loaded materials, if preload is active these materials do not contain any textures yet
            and have to be filled before rendering (by calling this function again, there is no need to save the prior
            returned list) or if return_random_element is True only a single Material is returned
    """
    # set default value
    if add_cp is None:
        add_cp = {}
    if used_assets is None:
        used_assets = []

    # makes the integration of complex materials easier
    addon_utils.enable("node_wrangler")

    haven_folder = Path(resolve_path(str(folder_path)))

    if preload and fill_used_empty_materials:
        raise RuntimeError("Preload and fill used empty materials can not be done at the same time, check config!")

    if not haven_folder.exists():
        raise FileNotFoundError(f"The given haven folder does not exist: {haven_folder}")

    # add the "textures" folder, if that is not already the case
    if haven_folder.name != "textures" and (haven_folder / "textures").exists():
        haven_folder = haven_folder / "textures"

    texture_names: List[str] = os.listdir(haven_folder)
    texture_names.sort()
    if not texture_names:
        raise FileNotFoundError(f"No texture folders found in {haven_folder}.")

    # filter texture names based on used assets:
    if used_assets:
        texture_names = [texture_name for texture_name in texture_names if
                         any(texture_name.startswith(asset) for asset in used_assets)]
        if not texture_names:
            raise FileNotFoundError(f"No texture folders found in {haven_folder} for which used_assets "
                                    f"can be meet: {used_assets}.")

    # if only one element is returned
    if return_random_element:
        texture_names = [random.choice(texture_names)]

    materials: List[Material] = []
    for texture_name in texture_names:       
        texture_folder_path = haven_folder / texture_name
        if not texture_folder_path.is_dir():
            print(f"Ignoring {texture_folder_path}, must be a folder.")
            continue

        texture_map_paths_by_type = identify_texture_maps(str(texture_folder_path))
        if texture_map_paths_by_type is None:
            print(f"Ignoring {texture_name}, could not identify texture maps.")
            continue
                
        # if the material was already created it only has to be searched
        if fill_used_empty_materials:
            new_mat = MaterialLoaderUtility.find_cc_material_by_name(texture_name, add_cp)
        else:
            new_mat = MaterialLoaderUtility.create_new_cc_material(texture_name, add_cp)
        # append newly created material
        materials.append(Material(new_mat))
        if preload:
            # if preload then the material is only created but not filled
            continue
        elif fill_used_empty_materials and not MaterialLoaderUtility.is_material_used(new_mat):
            # now only the materials, which have been used should be filled
            continue

        # create material based on the found image paths
        HavenMaterialLoader.create_material(new_mat, 
                                            texture_map_paths_by_type["base color"], 
                                            texture_map_paths_by_type["ambient occlusion"],
                                            texture_map_paths_by_type["specular"], 
                                            texture_map_paths_by_type["roughness"],
                                            texture_map_paths_by_type["transparency"], 
                                            texture_map_paths_by_type["normal"],
                                            texture_map_paths_by_type["displacement"], 
                                            texture_map_paths_by_type["bump"])
    if return_random_element:
        if len(materials) != 1:
            raise RuntimeError(f"The amount of loaded materials is not one: {materials}, this should not happen!")
        return materials[0]

    return materials


class HavenMaterialLoader:
    """
    This class loads all textures obtained from https://texturehaven.com, use 'blenderproc download haven'
    to download all the textures to your pc.

    All textures here support Physically based rendering (PBR), which makes the textures more realistic.

    There is a preload option, in which you only load empty materials, without any loaded textures, these are than
    later filled, when an object really uses them. This saves on loading times.
    """

    @staticmethod
    def create_material(new_mat: bpy.types.Material, base_image_path: str, ambient_occlusion_image_path: str, specular_image_path: str,
                        roughness_image_path: str, alpha_image_path: str, normal_image_path: str, displacement_image_path: str,
                        bump_image_path: str):
        """
        Create a material for the haven datatset, the combination used here is calibrated to the haven dataset format.

        :param new_mat: The new material, which will get all the given textures
        :param base_image_path: The path to the color image
        :param ambient_occlusion_image_path: The path to the ambient occlusion image
        :param specular_image_path: The path to the specular image
        :param roughness_image_path: The path to the roughness image
        :param alpha_image_path: The path to the alpha image (when this was written there was no alpha image provided \
                                 in the haven dataset)
        :param normal_image_path: The path to the normal image
        :param displacement_image_path: The path to the displacement image
        :param bump_image_path: The path to the bump image
        """
        nodes = new_mat.node_tree.nodes
        links = new_mat.node_tree.links

        principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
        output_node = Utility.get_the_one_node_with_type(nodes, "OutputMaterial")

        collection_of_texture_nodes = []
        base_color = MaterialLoaderUtility.add_base_color(nodes, links, base_image_path, principled_bsdf)
        collection_of_texture_nodes.append(base_color)

        specular_color = MaterialLoaderUtility.add_specular(nodes, links, specular_image_path, principled_bsdf)
        collection_of_texture_nodes.append(specular_color)

        ao_node = MaterialLoaderUtility.add_ambient_occlusion(nodes, links, ambient_occlusion_image_path,
                                                              principled_bsdf, base_color)
        collection_of_texture_nodes.append(ao_node)

        roughness_node = MaterialLoaderUtility.add_roughness(nodes, links, roughness_image_path,
                                                             principled_bsdf)
        collection_of_texture_nodes.append(roughness_node)

        alpha_node = MaterialLoaderUtility.add_alpha(nodes, links, alpha_image_path, principled_bsdf)
        collection_of_texture_nodes.append(alpha_node)

        # only add a bump map if no normal map was found
        if not os.path.exists(normal_image_path):
            bump_node = MaterialLoaderUtility.add_bump(nodes, links, bump_image_path, principled_bsdf)
            collection_of_texture_nodes.append(bump_node)
        else:
            normal_node = MaterialLoaderUtility.add_normal(nodes, links, normal_image_path, principled_bsdf,
                                                           invert_y_channel=False)
            collection_of_texture_nodes.append(normal_node)

        displacement_node = MaterialLoaderUtility.add_displacement(nodes, links, displacement_image_path,
                                                                   output_node)
        collection_of_texture_nodes.append(displacement_node)

        collection_of_texture_nodes = [node for node in collection_of_texture_nodes if node is not None]

        MaterialLoaderUtility.connect_uv_maps(nodes, links, collection_of_texture_nodes)
