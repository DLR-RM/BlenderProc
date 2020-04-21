
import os

import bpy

from src.main.Module import Module
from src.utility.Utility import Utility

class CCMaterialLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)


    def run(self):
        self._folder_path = Utility.resolve_path(self.config.get_string("folder_path", "resources/cctextures"))

        x_texture_node = -1500
        y_texture_node = 300
        if os.path.exists(self._folder_path) and os.path.isdir(self._folder_path):
            for asset in os.listdir(self._folder_path):
                current_path = os.path.join(self._folder_path, asset)
                if os.path.isdir(current_path):
                    base_image_path = os.path.join(current_path, "{}_2K_Color.jpg".format(asset))
                    if not os.path.exists(base_image_path):
                        continue
                    collection_of_texture_nodes = []
                    new_mat = bpy.data.materials.new(asset)
                    new_mat["is_cc_texture"] = True
                    new_mat.use_nodes = True
                    nodes = new_mat.node_tree.nodes
                    links = new_mat.node_tree.links

                    principled_bsdf = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
                    if principled_bsdf and len(principled_bsdf) == 1:
                        principled_bsdf = principled_bsdf[0]
                    else:
                        print("Warning: The generation of the new texture failed, it has more than one Prinicipled BSDF!")

                    output_node = Utility.get_nodes_with_type(nodes, "OutputMaterial")
                    if output_node and len(output_node) == 1:
                        output_node = output_node[0]
                    else:
                        print("Warning: The generation of the new texture failed, it has more than one Output Material!")


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
