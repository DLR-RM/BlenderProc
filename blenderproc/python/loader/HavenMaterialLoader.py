import glob
import os

import addon_utils
import bpy

from blenderproc.python.utility.Utility import resolve_path
from blenderproc.python.material import MaterialLoaderUtility
from blenderproc.python.utility.Utility import Utility

def load_haven_mat(folder_path: str = "resources/haven", used_assets: list = [], preload: bool = False, fill_used_empty_materials: bool = False, add_cp: dict = {}):
    """ Loads all specified haven textures from the given directory.

    :param folder_path: The path to the downloaded haven.
    :param used_assets: A list of all asset names, you want to use. The asset-name must not be typed in completely, only the
                        beginning the name starts with. By default all assets will be loaded, specified by an empty list.
    :param preload: If set true, only the material names are loaded and not the complete material.
    :param fill_used_empty_materials: If set true, the preloaded materials, which are used are now loaded completely.
    :param add_cp: A dictionary of materials and the respective properties.
    """
    # makes the integration of complex materials easier
    addon_utils.enable("node_wrangler")

    folder_path = resolve_path(folder_path)

    if preload and fill_used_empty_materials:
        raise Exception("Preload and fill used empty materials can not be done at the same time, check config!")
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for asset in os.listdir(folder_path):
            if used_assets:
                skip_this_one = True
                for used_asset in used_assets:
                    if asset.startswith(used_asset):
                        skip_this_one = False
                        break
                if skip_this_one:
                    continue
            current_path = os.path.join(folder_path, asset)
            if os.path.isdir(current_path):
                # find the current base_image_path by search for _diff_, this make it independent of the used res
                all_paths = glob.glob(os.path.join(current_path, "*.jpg"))
                base_image_path = ""
                for path in all_paths:
                    if "_diff_" in path:
                        base_image_path = path
                        break
                if not os.path.exists(base_image_path):
                    continue

                # if the material was already created it only has to be searched
                if fill_used_empty_materials:
                    new_mat = MaterialLoaderUtility.find_cc_material_by_name(asset, add_cp)
                else:
                    new_mat = MaterialLoaderUtility.create_new_cc_material(asset, add_cp)
                if preload:
                    # if preload then the material is only created but not filled
                    continue
                elif fill_used_empty_materials and not MaterialLoaderUtility.is_material_used(new_mat):
                    # now only the materials, which have been used should be filled
                    continue

                # construct all image paths
                # the images path contain the words named in this list, but some of them are differently
                # capitalized, e.g. Nor, NOR, NoR, ...
                used_elements = ["ao", "spec", "rough", "nor", "disp", "bump", "alpha"]
                final_paths = {}
                for ele in used_elements:
                    new_path = base_image_path.replace("diff", ele).lower()
                    found_path = ""
                    for path in all_paths:
                        if path.lower() == new_path:
                            found_path = path
                            break
                    final_paths[ele] = found_path

                # create material based on these image paths
                HavenMaterialLoader.create_material(new_mat, base_image_path, final_paths["ao"],
                                                    final_paths["spec"], final_paths["rough"],
                                                    final_paths["alpha"], final_paths["nor"],
                                                    final_paths["disp"], final_paths["bump"])
    else:
        raise Exception("The folder path does not exist: {}".format(folder_path))


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
