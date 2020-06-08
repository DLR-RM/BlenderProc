
import os

import bpy

from src.main.Module import Module
from src.utility.Utility import Utility
from src.provider.getter.Material import Material


class CCMaterialLoader(Module):
    """
    This modules loads all textures obtained from https://cc0textures.com, use the script
    (scripts/download_cc_textures.py) to download all the textures to your pc.

    All textures here support Physically based rendering (PBR), which makes the textures more realistic.

    All materials will have the custom property "is_cc_texture": True, which will make the selection later on easier.

    See the example section on how to use this in combination with a dataset: examples/shapenet_with_cctextures.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "folder_path", "The path to the downloaded cc0textures. Type: string. Default: resources/cctextures."
       "used_assets", "A list of all asset names, you want to use. The asset-name must not be typed in completely,"
                      "only the beginning the name starts with. By default all assets will be loaded, specified by"
                      "an empty list. Type: list. Default: []."
       "add_custom_properties", "A dictionary of materials and the respective properties."
                                "Type: dict. Default: {}."
       "preload", "If set true, only the material names are loaded and not the complete material."
                  "Type: bool. Default: False"
       "fill_used_empty_materials", "If set true, the preloaded materials, which are used are now loaded completely."
                                    "Type: bool. Default: False"
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self._folder_path = ""
        self._used_assets = []
        self._add_cp = {}
        self._preload = False
        self._fill_used_empty_materials = False


    def run(self):
        self._folder_path = Utility.resolve_path(self.config.get_string("folder_path", "resources/cctextures"))
        self._used_assets = self.config.get_list("used_assets", [])
        self._add_cp = self.config.get_raw_dict("add_custom_properties", {})
        self._preload = self.config.get_bool("preload", False)
        self._fill_used_empty_materials = self.config.get_bool("fill_used_empty_materials", False)

        if self._preload and self._fill_used_empty_materials:
            raise Exception("Preload and fill used empty materials can not be done at the same time, check config!")

        x_texture_node = -1500
        y_texture_node = 300
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

                    if self._fill_used_empty_materials:
                        # find used cc materials with this name
                        cond = {"cp_is_cc_texture": True, "cp_asset_name": asset}
                        for key, value in self._add_cp.items():
                            cond[key] = value
                        new_mats = Material.perform_and_condition_check(cond, [])
                        if len(new_mats) == 1:
                            new_mat = new_mats[0]
                        elif len(new_mats) > 1:
                            raise Exception("There was more than one material found!")
                        else:
                            # the material was not even loaded
                            continue
                        # check amount of usage of this material
                        if new_mat.users == 0:
                            # no one is using this material skip loading
                            continue
                        # only loads materials which are actually used
                        print("Fill material: {}".format(asset))
                    else:
                        # create a new material with the name of the asset
                        new_mat = bpy.data.materials.new(asset)
                        new_mat["is_cc_texture"] = True
                        new_mat["asset_name"] = asset
                        new_mat.use_nodes = True
                        for key, value in self._add_cp.items():
                            cp_key = key
                            if key.startswith("cp_"):
                                cp_key = key[len("cp_"):]
                            else:
                                raise Exception("All cp have to start with cp_")
                            new_mat[cp_key] = value
                    if self._preload:
                        continue
                    collection_of_texture_nodes = []

                    nodes = new_mat.node_tree.nodes
                    links = new_mat.node_tree.links

                    principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                    output_node = Utility.get_the_one_node_with_type(nodes, "OutputMaterial")

                    base_color = nodes.new('ShaderNodeTexImage')
                    base_color.image = bpy.data.images.load(base_image_path, check_existing=True)
                    base_color.location.x = x_texture_node
                    base_color.location.y = y_texture_node
                    collection_of_texture_nodes.append(base_color)

                    links.new(base_color.outputs["Color"], principled_bsdf.inputs["Base Color"])

                    principled_bsdf.inputs["Specular"].default_value = 0.333

                    ambient_occlusion_image_path = base_image_path.replace("Color", "AmbientOcclusion")
                    if os.path.exists(ambient_occlusion_image_path):
                        ao_color = nodes.new('ShaderNodeTexImage')
                        ao_color.image = bpy.data.images.load(ambient_occlusion_image_path, check_existing=True)
                        ao_color.location.x = x_texture_node
                        ao_color.location.y = y_texture_node * 2
                        collection_of_texture_nodes.append(ao_color)

                        math_node = nodes.new(type='ShaderNodeMixRGB')
                        math_node.blend_type = "MULTIPLY"
                        math_node.location.x = x_texture_node * 0.5
                        math_node.location.y = y_texture_node * 1.5
                        math_node.inputs["Fac"].default_value = 0.333

                        links.new(base_color.outputs["Color"], math_node.inputs[1])
                        links.new(ao_color.outputs["Color"], math_node.inputs[2])
                        links.new(math_node.outputs["Color"], principled_bsdf.inputs["Base Color"])

                    metalness_image_path = base_image_path.replace("Color", "Metalness")
                    if os.path.exists(metalness_image_path):
                        metalness_texture = nodes.new('ShaderNodeTexImage')
                        metalness_texture.image = bpy.data.images.load(metalness_image_path, check_existing=True)
                        metalness_texture.location.x = x_texture_node
                        metalness_texture.location.y = y_texture_node * 0
                        collection_of_texture_nodes.append(metalness_texture)

                        links.new(metalness_texture.outputs["Color"], principled_bsdf.inputs["Metallic"])

                    roughness_image_path = base_image_path.replace("Color", "Roughness")
                    if os.path.exists(roughness_image_path):
                        roughness_texture = nodes.new('ShaderNodeTexImage')
                        roughness_texture.image = bpy.data.images.load(roughness_image_path, check_existing=True)
                        roughness_texture.location.x = x_texture_node
                        roughness_texture.location.y = y_texture_node * -1
                        collection_of_texture_nodes.append(roughness_texture)

                        links.new(roughness_texture.outputs["Color"], principled_bsdf.inputs["Roughness"])

                    alpha_image_path = base_image_path.replace("Color", "Opacity")
                    if os.path.exists(alpha_image_path):
                        alpha_texture = nodes.new('ShaderNodeTexImage')
                        alpha_texture.image = bpy.data.images.load(alpha_image_path, check_existing=True)
                        alpha_texture.location.x = x_texture_node
                        alpha_texture.location.y = y_texture_node * -2
                        collection_of_texture_nodes.append(alpha_texture)

                        links.new(alpha_texture.outputs["Color"], principled_bsdf.inputs["Alpha"])

                    normal_image_path = base_image_path.replace("Color", "Normal")
                    normal_y_value = y_texture_node * -3
                    if os.path.exists(normal_image_path):
                        normal_texture = nodes.new('ShaderNodeTexImage')
                        normal_texture.image = bpy.data.images.load(normal_image_path, check_existing=True)
                        normal_texture.location.x = x_texture_node
                        normal_texture.location.y = normal_y_value
                        collection_of_texture_nodes.append(normal_texture)
                        direct_x_mode = True
                        if direct_x_mode:

                            separate_rgba = nodes.new('ShaderNodeSeparateRGB')
                            separate_rgba.location.x = 4.0/5.0 * x_texture_node
                            separate_rgba.location.y = normal_y_value
                            links.new(normal_texture.outputs["Color"], separate_rgba.inputs["Image"])

                            invert_node = nodes.new("ShaderNodeInvert")
                            invert_node.inputs["Fac"].default_value = 1.0
                            invert_node.location.x = 3.0/5.0 * x_texture_node
                            invert_node.location.y = normal_y_value

                            links.new(separate_rgba.outputs["G"], invert_node.inputs["Color"])

                            combine_rgba = nodes.new('ShaderNodeCombineRGB')
                            combine_rgba.location.x = 2.0/5.0 * x_texture_node
                            combine_rgba.location.y = normal_y_value
                            links.new(separate_rgba.outputs["R"], combine_rgba.inputs["R"])
                            links.new(invert_node.outputs["Color"], combine_rgba.inputs["G"])
                            links.new(separate_rgba.outputs["B"], combine_rgba.inputs["B"])

                            current_output = combine_rgba.outputs["Image"]
                        else:
                            current_output = normal_texture.outputs["Color"]

                        normal_map = nodes.new("ShaderNodeNormalMap")
                        # TODO figure out the correct value here
                        normal_map.inputs["Strength"].default_value = 2.0
                        normal_map.location.x = 1.0 / 5.0 * x_texture_node
                        normal_map.location.y = normal_y_value
                        links.new(current_output, normal_map.inputs["Color"])
                        links.new(normal_map.outputs["Normal"], principled_bsdf.inputs["Normal"])


                    displacement_image_path = base_image_path.replace("Color", "Displacement")
                    if os.path.exists(displacement_image_path):
                        displacement_texture = nodes.new('ShaderNodeTexImage')
                        displacement_texture.image = bpy.data.images.load(displacement_image_path, check_existing=True)
                        displacement_texture.location.x = x_texture_node
                        displacement_texture.location.y = y_texture_node * -4
                        collection_of_texture_nodes.append(displacement_texture)

                        displacement_node = nodes.new("ShaderNodeDisplacement")
                        displacement_node.inputs["Midlevel"].default_value = 0.5
                        displacement_node.inputs["Scale"].default_value = 0.05
                        displacement_node.location.x = x_texture_node * 0.5
                        displacement_node.location.y = y_texture_node * -4
                        links.new(displacement_texture.outputs["Color"], displacement_node.inputs["Height"])
                        links.new(displacement_node.outputs["Displacement"], output_node.inputs["Displacement"])


                    if len(collection_of_texture_nodes) > 0:
                        texture_coords = nodes.new("ShaderNodeTexCoord")
                        texture_coords.location.x = x_texture_node * 1.4
                        mapping_node = nodes.new("ShaderNodeMapping")
                        mapping_node.location.x = x_texture_node * 1.2

                        links.new(texture_coords.outputs["UV"], mapping_node.inputs["Vector"])
                        for texture_node in collection_of_texture_nodes:
                            links.new(mapping_node.outputs["Vector"], texture_node.inputs["Vector"])
