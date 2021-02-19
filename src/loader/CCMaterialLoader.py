import os

from src.utility.MaterialLoaderUtility import MaterialLoaderUtility
from src.main.Module import Module
from src.utility.Utility import Utility


class CCMaterialLoader(Module):
    """
    This modules loads all textures obtained from https://cc0textures.com, use the script
    (scripts/download_cc_textures.py) to download all the textures to your pc.

    All textures here support Physically based rendering (PBR), which makes the textures more realistic.

    All materials will have the custom property "is_cc_texture": True, which will make the selection later on easier.

    See the example section on how to use this in combination with a dataset: examples/shapenet_with_cctextures.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - folder_path
          - The path to the downloaded cc0textures. Default: resources/cctextures.
          - string
        * - used_assets
          - A list of all asset names, you want to use. The asset-name must not be typed in completely, only the
            beginning the name starts with. By default all assets will be loaded, specified by an empty list.
            Default: [].
          - list
        * - use_all_materials
          - If this is true all materials, which are available are used. This includes materials, which are not
            tileable an materials which have an alpha channel. By default only a reasonable selection is used.
            Default: False
          - bool
        * - add_custom_properties
          - A dictionary of materials and the respective properties. Default: {}.
          - dict
        * - preload
          - If set true, only the material names are loaded and not the complete material. Default: False
          - bool
        * - fill_used_empty_materials
          - If set true, the preloaded materials, which are used are now loaded completely. Default: False
          - bool
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self._folder_path = ""
        self._probably_useful_texture = ["paving stones", "tiles", "wood", "fabric", "bricks", "metal", "wood floor",
                                         "ground", "rock", "concrete", "leather", "planks", "rocks", "gravel",
                                         "asphalt", "painted metal", "painted plaster", "marble", "carpet",
                                         "plastic", "roofing tiles", "bark", "metal plates", "wood siding",
                                         "terrazzo", "plaster", "paint", "corrugated steel", "painted wood", "lava"
                                         "cardboard", "clay", "diamond plate", "ice", "moss", "pipe", "candy",
                                         "chipboard", "rope", "sponge", "tactile paving", "paper", "cork",
                                         "wood chips"]
        self._use_all_materials = False
        self._used_assets = []
        self._add_cp = {}
        self._preload = False
        self._fill_used_empty_materials = False

    def run(self):
        self._folder_path = Utility.resolve_path(self.config.get_string("folder_path", "resources/cctextures"))
        if self.config.has_param("use_all_materials") and self.config.has_param("used_assets"):
            raise Exception("It is impossible to use all materials and selected a certain list of assets!")
        self._use_all_materials = self.config.get_bool("use_all_materials", False)
        if not self._use_all_materials:
            self._used_assets = self._probably_useful_texture
        else:
            self._used_assets = self.config.get_list("used_assets", [])
        self._add_cp = self.config.get_raw_dict("add_custom_properties", {})
        self._preload = self.config.get_bool("preload", False)
        self._fill_used_empty_materials = self.config.get_bool("fill_used_empty_materials", False)

        if self._preload and self._fill_used_empty_materials:
            raise Exception("Preload and fill used empty materials can not be done at the same time, check config!")

        if os.path.exists(self._folder_path) and os.path.isdir(self._folder_path):
            for asset in os.listdir(self._folder_path):
                if self._used_assets:
                    skip_this_one = True
                    for used_asset in self._used_assets:
                        if asset.startswith(used_asset):
                            skip_this_one = False
                            break
                    if skip_this_one:
                        continue
                current_path = os.path.join(self._folder_path, asset)
                if os.path.isdir(current_path):
                    base_image_path = os.path.join(current_path, "{}_2K_Color.jpg".format(asset))
                    if not os.path.exists(base_image_path):
                        continue

                    # if the material was already created it only has to be searched
                    if self._fill_used_empty_materials:
                        new_mat = MaterialLoaderUtility.find_cc_material_by_name(asset, self._add_cp)
                    else:
                        new_mat = MaterialLoaderUtility.create_new_cc_material(asset, self._add_cp)
                    if self._preload:
                        # if preload then the material is only created but not filled
                        continue
                    elif self._fill_used_empty_materials and not MaterialLoaderUtility.is_material_used(new_mat):
                        # now only the materials, which have been used should be filled
                        continue

                    # construct all image paths
                    ambient_occlusion_image_path = base_image_path.replace("Color", "AmbientOcclusion")
                    metallic_image_path = base_image_path.replace("Color", "Metalness")
                    roughness_image_path = base_image_path.replace("Color", "Roughness")
                    alpha_image_path = base_image_path.replace("Color", "Opacity")
                    normal_image_path = base_image_path.replace("Color", "Normal")
                    displacement_image_path = base_image_path.replace("Color", "Displacement")

                    # create material based on these image paths
                    CCMaterialLoader.create_material(new_mat, base_image_path, ambient_occlusion_image_path,
                                                     metallic_image_path, roughness_image_path, alpha_image_path,
                                                     normal_image_path, displacement_image_path)
        else:
            raise Exception("The folder path does not exist: {}".format(self._folder_path))

    @staticmethod
    def create_material(new_mat, base_image_path, ambient_occlusion_image_path, metallic_image_path,
                        roughness_image_path, alpha_image_path, normal_image_path, displacement_image_path):
        """
        Create a material for the cctexture datatset, the combination used here is calibrated to this.

        :param new_mat: The new material, which will get all the given textures
        :param base_image_path: The path to the color image
        :param ambient_occlusion_image_path: The path to the ambient occlusion image
        :param metallic_image_path: The path to the metallic image
        :param roughness_image_path: The path to the roughness image
        :param alpha_image_path: The path to the alpha image (when this was written there was no alpha image provided \
                                 in the haven dataset)
        :param normal_image_path: The path to the normal image
        :param displacement_image_path: The path to the displacement image
        """
        nodes = new_mat.node_tree.nodes
        links = new_mat.node_tree.links

        principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
        output_node = Utility.get_the_one_node_with_type(nodes, "OutputMaterial")

        collection_of_texture_nodes = []
        base_color = MaterialLoaderUtility.add_base_color(nodes, links, base_image_path, principled_bsdf)
        collection_of_texture_nodes.append(base_color)

        principled_bsdf.inputs["Specular"].default_value = 0.333

        ao_node = MaterialLoaderUtility.add_ambient_occlusion(nodes, links, ambient_occlusion_image_path,
                                                              principled_bsdf, base_color)
        collection_of_texture_nodes.append(ao_node)

        metallic_node = MaterialLoaderUtility.add_metal(nodes, links, metallic_image_path,
                                                        principled_bsdf)
        collection_of_texture_nodes.append(metallic_node)

        roughness_node = MaterialLoaderUtility.add_roughness(nodes, links, roughness_image_path,
                                                             principled_bsdf)
        collection_of_texture_nodes.append(roughness_node)

        alpha_node = MaterialLoaderUtility.add_alpha(nodes, links, alpha_image_path, principled_bsdf)
        collection_of_texture_nodes.append(alpha_node)

        normal_node = MaterialLoaderUtility.add_normal(nodes, links, normal_image_path, principled_bsdf,
                                                       invert_y_channel=True)
        collection_of_texture_nodes.append(normal_node)

        displacement_node = MaterialLoaderUtility.add_displacement(nodes, links, displacement_image_path,
                                                                   output_node)
        collection_of_texture_nodes.append(displacement_node)

        collection_of_texture_nodes = [node for node in collection_of_texture_nodes if node is not None]

        MaterialLoaderUtility.connect_uv_maps(nodes, links, collection_of_texture_nodes)
