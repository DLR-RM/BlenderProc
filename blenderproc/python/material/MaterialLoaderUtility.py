import os
import random
from typing import Union, List, Optional

import bpy

from blenderproc.python.modules.provider.getter.Material import Material as MaterialGetter
from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.utility.Utility import Utility

x_texture_node = -1500
y_texture_node = 300


def collect_all() -> List[Optional["Material"]]:
    """ Returns all existing materials.

    :return: A list of all materials.
    """
    return convert_to_materials(bpy.data.materials)


def create(name: str) -> "Material":
    """ Creates a new empty material.

    :param name: The name of the new material.
    :return: The new material.
    """
    new_mat = bpy.data.materials.new(name=name)
    new_mat.use_nodes = True
    return Material(new_mat)


def convert_to_materials(blender_materials: List[Optional[bpy.types.Material]]) -> List[Optional["Material"]]:
    """ Converts the given list of blender materials to bproc.Material(s)

    :param blender_materials: List of materials.
    :return: The list of materials.
    """
    return [(None if obj is None else Material(obj)) for obj in blender_materials]


def find_cc_material_by_name(material_name: str, custom_properties: dict):
    """
    Finds from all loaded materials the cc material, which has the given material_name and the given
    custom_properties.

    :param material_name: Name of the searched material
    :param custom_properties: Custom properties, which have been assigned before
    :return: bpy.types.Material: Return the searched material, if not found returns None
    """
    # find used cc materials with this name
    cond = {"cp_is_cc_texture": True, "cp_asset_name": material_name}
    for key, value in custom_properties.items():
        cond[key] = value
    new_mats = MaterialGetter.perform_and_condition_check(cond, [])
    if len(new_mats) == 1:
        new_mat = new_mats[0]
        return new_mat
    elif len(new_mats) > 1:
        raise Exception("There was more than one material found!")
    else:
        # the material was not even loaded
        return None


def is_material_used(material: bpy.types.Material):
    """
    Checks if the given material is used on any object.

    :param material: Material, which should be checked
    :return: True if the material is used
    """
    # check amount of usage of this material
    return material.users != 0


def create_new_cc_material(material_name: str, add_custom_properties: dict):
    """
    Creates a new material, which gets the given custom properties and the material name.

    :param material_name: The name of the material
    :param add_custom_properties: The custom properties, which should be added to the material
    :return: bpy.types.Material: Return the newly created material
    """
    # create a new material with the name of the asset
    new_mat = bpy.data.materials.new(material_name)
    new_mat["is_cc_texture"] = True
    new_mat["asset_name"] = material_name
    new_mat.use_nodes = True
    for key, value in add_custom_properties.items():
        if key.startswith("cp_"):
            cp_key = key[len("cp_"):]
        else:
            raise Exception("All cp have to start with cp_")
        new_mat[cp_key] = value
    return new_mat


def create_image_node(nodes: bpy.types.Nodes, image: Union[str, bpy.types.Image], non_color_mode=False, x_location=0,
                      y_location=0):
    """
    Creates a texture image node inside of a material.

    :param nodes: Nodes from the current material
    :param image: Either the path to the image which should be loaded or the bpy.types.Image
    :param non_color_mode: If this True, the color mode of the image will be "Non-Color"
    :param x_location: X Location in the node tree
    :param y_location: Y Location in the node tree
    :return: bpy.type.Node: Return the newly constructed image node
    """
    image_node = nodes.new('ShaderNodeTexImage')
    if isinstance(image, bpy.types.Image):
        image_node.image = image
    else:
        image_node.image = bpy.data.images.load(image, check_existing=True)
    if non_color_mode:
        image_node.image.colorspace_settings.name = 'Non-Color'
    image_node.location.x = x_location
    image_node.location.y = y_location
    return image_node


def add_base_color(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, base_image_path,
                   principled_bsdf: bpy.types.Node):
    """
    Adds base color to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param base_image_path: Path to the base image
    :param principled_bsdf: Principled BSDF node of the current material
    :return: bpy.types.Node: The newly constructed texture node
    """
    if os.path.exists(base_image_path):
        base_color = create_image_node(nodes, base_image_path, False,
                                       x_texture_node,
                                       y_texture_node)
        links.new(base_color.outputs["Color"], principled_bsdf.inputs["Base Color"])
        return base_color
    return None


def add_ambient_occlusion(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, ambient_occlusion_image_path,
                          principled_bsdf: bpy.types.Node, base_color: bpy.types.Node):
    """
    Adds ambient occlusion to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param ambient_occlusion_image_path: Path to the ambient occlusion image
    :param principled_bsdf: Principled BSDF node of the current material
    :param base_color: Base color node of the current material
    :return: bpy.types.Node: The newly constructed texture node
    """
    if os.path.exists(ambient_occlusion_image_path):
        ao_color = create_image_node(nodes, ambient_occlusion_image_path, True,
                                     x_texture_node,
                                     y_texture_node * 2)
        math_node = nodes.new(type='ShaderNodeMixRGB')
        math_node.blend_type = "MULTIPLY"
        math_node.location.x = x_texture_node * 0.5
        math_node.location.y = y_texture_node * 1.5
        math_node.inputs["Fac"].default_value = 0.333

        links.new(base_color.outputs["Color"], math_node.inputs[1])
        links.new(ao_color.outputs["Color"], math_node.inputs[2])
        links.new(math_node.outputs["Color"], principled_bsdf.inputs["Base Color"])

        return ao_color
    return None


def add_metal(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, metalness_image_path: str,
              principled_bsdf: bpy.types.Node):
    """
    Adds metal to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param metalness_image_path: Path to the metal image
    :param principled_bsdf: Principled BSDF node of the current material
    :return: bpy.types.Node: The newly constructed texture node
    """
    if os.path.exists(metalness_image_path):
        metallic = create_image_node(nodes, metalness_image_path, True,
                                     x_texture_node, 0)
        links.new(metallic.outputs["Color"], principled_bsdf.inputs["Metallic"])
        return metallic
    return None


def add_roughness(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, roughness_image_path: str,
                  principled_bsdf: bpy.types.Node):
    """
    Adds roughness to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param roughness_image_path: Path to the metal image
    :param principled_bsdf: Principled BSDF node of the current material
    :return: bpy.types.Node: The newly constructed texture node
    """
    if os.path.exists(roughness_image_path):
        roughness_texture = create_image_node(nodes, roughness_image_path, True,
                                              x_texture_node,
                                              y_texture_node * -1)
        links.new(roughness_texture.outputs["Color"], principled_bsdf.inputs["Roughness"])
        return roughness_texture
    return None


def add_specular(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, specular_image_path: str,
                 principled_bsdf: bpy.types.Node):
    """
    Adds specular to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param specular_image_path: Path to the metal image
    :param principled_bsdf: Principled BSDF node of the current material
    :return: bpy.types.Node: The newly constructed texture node
    """
    if os.path.exists(specular_image_path):
        specular_texture = create_image_node(nodes, specular_image_path, True,
                                             x_texture_node, 0)
        links.new(specular_texture.outputs["Color"], principled_bsdf.inputs["Specular"])
        return specular_texture
    return None


def add_alpha(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, alpha_image_path: str,
              principled_bsdf: bpy.types.Node):
    """
    Adds alpha to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param alpha_image_path: Path to the metal image
    :param principled_bsdf: Principled BSDF node of the current material
    :return: bpy.types.Node: The newly constructed texture node
    """
    if os.path.exists(alpha_image_path):
        alpha_texture = create_image_node(nodes, alpha_image_path, True,
                                          x_texture_node,
                                          y_texture_node * -2)
        links.new(alpha_texture.outputs["Color"], principled_bsdf.inputs["Alpha"])
        return alpha_texture
    return None


def add_normal(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, normal_image_path: str,
               principled_bsdf: bpy.types.Node, invert_y_channel: bool):
    """
    Adds normal to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param normal_image_path: Path to the metal image
    :param principled_bsdf: Principled BSDF node of the current material
    :param invert_y_channel: If this is True the Y Color Channel is inverted.
    :return: bpy.types.Node: The newly constructed texture node
    """
    normal_y_value = y_texture_node * -3
    if os.path.exists(normal_image_path):
        normal_texture = create_image_node(nodes, normal_image_path, True,
                                           x_texture_node,
                                           normal_y_value)
        if invert_y_channel:

            separate_rgba = nodes.new('ShaderNodeSeparateRGB')
            separate_rgba.location.x = 4.0 / 5.0 * x_texture_node
            separate_rgba.location.y = normal_y_value
            links.new(normal_texture.outputs["Color"], separate_rgba.inputs["Image"])

            invert_node = nodes.new("ShaderNodeInvert")
            invert_node.inputs["Fac"].default_value = 1.0
            invert_node.location.x = 3.0 / 5.0 * x_texture_node
            invert_node.location.y = normal_y_value

            links.new(separate_rgba.outputs["G"], invert_node.inputs["Color"])

            combine_rgba = nodes.new('ShaderNodeCombineRGB')
            combine_rgba.location.x = 2.0 / 5.0 * x_texture_node
            combine_rgba.location.y = normal_y_value
            links.new(separate_rgba.outputs["R"], combine_rgba.inputs["R"])
            links.new(invert_node.outputs["Color"], combine_rgba.inputs["G"])
            links.new(separate_rgba.outputs["B"], combine_rgba.inputs["B"])

            current_output = combine_rgba.outputs["Image"]
        else:
            current_output = normal_texture.outputs["Color"]

        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.inputs["Strength"].default_value = 1.0
        normal_map.location.x = 1.0 / 5.0 * x_texture_node
        normal_map.location.y = normal_y_value
        links.new(current_output, normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], principled_bsdf.inputs["Normal"])
        return normal_texture
    return None


def add_bump(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, bump_image_path: str,
             principled_bsdf: bpy.types.Node):
    """
    Adds bump to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param bump_image_path: Path to the metal image
    :param principled_bsdf: Principled BSDF node of the current material
    :return: bpy.types.Node: The newly constructed texture node
    """
    bump_y_value = y_texture_node * -3
    if os.path.exists(bump_image_path):
        bump_texture = create_image_node(nodes, bump_image_path, True,
                                         x_texture_node,
                                         bump_y_value)
        bump_map = nodes.new("ShaderNodeBumpMap")
        bump_map.inputs["Strength"].default_value = 1.0
        bump_map.location.x = 1.0 / 5.0 * x_texture_node
        bump_map.location.y = bump_y_value
        links.new(bump_texture.outputs["Color"], bump_map.inputs["Heights"])
        links.new(bump_map.outputs["Normal"], principled_bsdf.inputs["Normal"])
        return bump_texture
    return None


def add_displacement(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, displacement_image_path: str,
                     output_node: bpy.types.Node):
    """
    Adds bump to the principled bsdf node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param displacement_image_path: Path to the metal image
    :param output_node: Output node of the current material
    :return: bpy.types.Node: The newly constructed texture node
    """
    if os.path.exists(displacement_image_path):
        displacement_texture = create_image_node(nodes, displacement_image_path, True,
                                                 x_texture_node,
                                                 y_texture_node * -4)
        displacement_node = nodes.new("ShaderNodeDisplacement")
        displacement_node.inputs["Midlevel"].default_value = 0.5
        displacement_node.inputs["Scale"].default_value = 0.15
        displacement_node.location.x = x_texture_node * 0.5
        displacement_node.location.y = y_texture_node * -4
        links.new(displacement_texture.outputs["Color"], displacement_node.inputs["Height"])
        links.new(displacement_node.outputs["Displacement"], output_node.inputs["Displacement"])
        return displacement_texture
    return None


def connect_uv_maps(nodes: bpy.types.Nodes, links: bpy.types.NodeLinks, collection_of_texture_nodes: list):
    """
    Connect all given texture nodes to a newly constructed UV node.

    :param nodes: Nodes from the current material
    :param links: Links from the current material
    :param collection_of_texture_nodes: List of :class: `bpy.type.Node` of type :class: `ShaderNodeTexImage`
    """
    if len(collection_of_texture_nodes) > 0:
        texture_coords = nodes.new("ShaderNodeTexCoord")
        texture_coords.location.x = x_texture_node * 1.4
        mapping_node = nodes.new("ShaderNodeMapping")
        mapping_node.location.x = x_texture_node * 1.2

        links.new(texture_coords.outputs["UV"], mapping_node.inputs["Vector"])
        for texture_node in collection_of_texture_nodes:
            if texture_node is not None:
                links.new(mapping_node.outputs["Vector"], texture_node.inputs["Vector"])


def add_alpha_channel_to_textures(blurry_edges):
    """
    Adds transparency to all textures, which contain an .png image as an image input

    :param blurry_edges: If True, the edges of the alpha channel might be blurry,
                            this causes errors if the alpha channel should only be 0 or 1

    Be careful, when you replace the original texture with something else (Segmentation, ...),
    the necessary texture node gets lost. By copying it into a new material as done in the SegMapRenderer, you
    can keep the transparency even for those nodes.

    """
    obj_with_mats = [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]
    visited_materials = set()
    # walk over all objects, which have materials
    for obj in obj_with_mats:
        for slot in obj.material_slots:
            material = slot.material
            if material is None:
                # this can happen if a material slot was created but no material was assigned
                continue
            if material.name in visited_materials:
                # skip a material if it has been used before
                continue
            visited_materials.add(material.name)
            texture_node = None
            # check each node of the material
            for node in material.node_tree.nodes:
                # if it is a texture image node
                if 'TexImage' in node.bl_idname:
                    if '.png' in node.image.name:  # contains an alpha channel
                        texture_node = node
            # this material contains an alpha png texture
            if texture_node is not None:
                nodes = material.node_tree.nodes
                links = material.node_tree.links
                node_connected_to_the_output, material_output = \
                    Utility.get_node_connected_to_the_output_and_unlink_it(material)

                if node_connected_to_the_output is not None:
                    mix_node = nodes.new(type='ShaderNodeMixShader')

                    # avoid blurry edges on the edges important for Normal, SegMapRenderer and others
                    if blurry_edges:
                        # add the alpha channel of the image to the mix shader node as a factor
                        links.new(texture_node.outputs['Alpha'], mix_node.inputs['Fac'])
                    else:
                        # Map all alpha values to 0 or 1 by applying the step function: 1 if x > 0.5 else 0
                        step_function_node = nodes.new("ShaderNodeMath")
                        step_function_node.operation = "GREATER_THAN"
                        links.new(texture_node.outputs['Alpha'], step_function_node.inputs['Value'])
                        links.new(step_function_node.outputs['Value'], mix_node.inputs['Fac'])

                    links.new(node_connected_to_the_output.outputs[0], mix_node.inputs[2])
                    transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
                    links.new(transparent_node.outputs['BSDF'], mix_node.inputs[1])
                    # connect to material output
                    links.new(mix_node.outputs['Shader'], material_output.inputs['Surface'])
                else:
                    raise Exception("Could not find shader node, which is connected to the material output "
                                    "for: {}".format(slot.name))


def add_alpha_texture_node(used_material, new_material):
    """
    Adds to a predefined new_material a texture node from an existing material (used_material)
    This is necessary to connect it later on in the add_alpha_channel_to_textures

    :param used_material: existing material, which might contain a texture node with a .png texture
    :param new_material: a new material, which will get a copy of this texture node
    :return: the modified new_material, if no texture node was found, the original new_material
    """
    if used_material is None:
        # this can happen if a material slot was created but no material was assigned
        return used_material
    # find out if there is an .png file used here
    texture_node = None
    for node in used_material.node_tree.nodes:
        # if it is a texture image node
        if 'TexImage' in node.bl_idname:
            if '.png' in node.image.name:  # contains an alpha channel
                texture_node = node
    # this material contains an alpha png texture
    if texture_node is not None:
        new_mat_alpha = new_material.copy()  # copy the material
        nodes = new_mat_alpha.node_tree.nodes
        # copy the texture node into the new material to make sure it is used
        new_tex_node = nodes.new(type='ShaderNodeTexImage')
        new_tex_node.image = texture_node.image
        # use the new material
        return new_mat_alpha
    return new_material


def change_to_texture_less_render(use_alpha_channel):
    """ Changes the materials, which do not contain a emission shader to a white slightly glossy texture

    :param use_alpha_channel: If true, the alpha channel stored in .png textures is used.
    """
    new_mat = bpy.data.materials.new(name="TextureLess")
    new_mat.use_nodes = True
    nodes = new_mat.node_tree.nodes

    principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")

    # setting the color values for the shader
    principled_bsdf.inputs['Specular'].default_value = 0.65  # specular
    principled_bsdf.inputs['Roughness'].default_value = 0.2  # roughness

    for object in [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]:
        # replace all materials with the new texture less material
        for slot in object.material_slots:
            emission_shader = False
            # check if the material contains an emission shader:
            for node in slot.material.node_tree.nodes:
                # check if one of the shader nodes is a Emission Shader
                if 'Emission' in node.bl_idname:
                    emission_shader = True
                    break
            # only replace materials, which do not contain any emission shader
            if not emission_shader:
                if use_alpha_channel:
                    slot.material = add_alpha_texture_node(slot.material, new_mat)
                else:
                    slot.material = new_mat


def create_procedural_texture(pattern_name: str = None) -> bpy.types.Texture:
    """ Creates a new procedural texture based on a specified pattern.

    :param pattern_name: The name of the pattern. Available: ["CLOUDS", "DISTORTED_NOISE", "MAGIC", "MARBLE", "MUSGRAVE", "NOISE", "STUCCI", "VORONOI", "WOOD"]
                            If None is given, a random pattern is used.
    :return: The created texture
    """
    possible_patterns = ["CLOUDS", "DISTORTED_NOISE", "MAGIC", "MARBLE", "MUSGRAVE", "NOISE", "STUCCI",
                         "VORONOI", "WOOD"]

    # If no pattern has been given, use a random one, otherwise check whether the given pattern is valid.
    if pattern_name is None:
        pattern_name = random.choice(possible_patterns)
    else:
        pattern_name = pattern_name.upper()
        if pattern_name not in possible_patterns:
            raise Exception(
                "There is no such pattern: " + str(pattern_name) + ". Allowed patterns are: " + str(possible_patterns))

    return bpy.data.textures.new("ct_{}".format(pattern_name), pattern_name)
