import warnings
from typing import List

from blenderproc.python.types.MaterialUtility import Material
import bpy
import random

def add_dust(material: Material, strength: float, texture_nodes: List[bpy.types.Texture] = None, texture_scale: float = 0.1):
    """ Adds a dust film to the material, where the strength determines how much dust is used.

    This will be added right before the output of the material.

    :param material: Used material
    :param strength: This determines the strength of the dust, 0 means no dust 1.0 means full dust. Values above 1.0 are
                        possible, but create a thick film out of dust, which hides the material completely.
    :param texture_nodes: If a specific dust texture should be used, this can be specified.  If this is empty a random noise texture is generated.
    :param texture_scale: This scale is used to scale down the used noise texture (even for the case where a random noise texture
                            is used).
    """

    group_node = material.new_node("ShaderNodeGroup")
    group_node.width = 250
    group = bpy.data.node_groups.new(name="Dust Material", type="ShaderNodeTree")
    group_node.node_tree = group
    nodes, links = group.nodes, group.links

    # define start locations and differences, to make the debugging easier
    x_pos, x_diff = -(250 * 4), 250
    y_pos, y_diff = (x_diff * 1), x_diff

    # Extract the normal for the current material location
    geometry_node = nodes.new('ShaderNodeNewGeometry')
    geometry_node.location.x = x_pos + x_diff * 0
    geometry_node.location.y = y_pos
    # this node clips the values, to avoid negative values in the usage below
    clip_mix_node = nodes.new("ShaderNodeMixRGB")
    clip_mix_node.inputs["Fac"].default_value = 1.0
    clip_mix_node.use_clamp = True
    clip_mix_node.location.x = x_pos + x_diff * 1
    clip_mix_node.location.y = y_pos
    links.new(geometry_node.outputs["Normal"], clip_mix_node.inputs["Color2"])

    # use only the z component
    separate_z_normal = nodes.new("ShaderNodeSeparateRGB")
    separate_z_normal.location.x = x_pos + x_diff * 2
    separate_z_normal.location.y = y_pos
    links.new(clip_mix_node.outputs["Color"], separate_z_normal.inputs["Image"])

    # this layer weight adds a small fresnel around the object, which makes it more realistic
    layer_weight = nodes.new("ShaderNodeLayerWeight")
    layer_weight.location.x = x_pos + x_diff * 2
    layer_weight.location.y = y_pos - y_diff * 1
    layer_weight.inputs["Blend"].default_value = 0.5
    # combine it with the z component
    mix_with_layer_weight = nodes.new("ShaderNodeMixRGB")
    mix_with_layer_weight.location.x = x_pos + x_diff * 3
    mix_with_layer_weight.location.y = y_pos
    mix_with_layer_weight.inputs["Fac"].default_value = 0.2
    links.new(separate_z_normal.outputs["B"], mix_with_layer_weight.inputs["Color1"])
    links.new(layer_weight.outputs["Facing"], mix_with_layer_weight.inputs["Color2"])
    # add a gamma node, to scale the colors correctly
    gamma_node = nodes.new("ShaderNodeGamma")
    gamma_node.location.x = x_pos + x_diff * 4
    gamma_node.location.y = y_pos
    gamma_node.inputs["Gamma"].default_value = 2.2
    links.new(mix_with_layer_weight.outputs["Color"], gamma_node.inputs["Color"])

    # use an overlay node to combine it with the texture result
    overlay = nodes.new("ShaderNodeMixRGB")
    overlay.location.x = x_pos + x_diff * 5
    overlay.location.y = y_pos
    overlay.blend_type = "OVERLAY"
    overlay.inputs["Fac"].default_value = 1.0
    links.new(gamma_node.outputs["Color"], overlay.inputs["Color1"])

    # add a multiply node to scale down or up the strength of the dust
    multiply_node = nodes.new("ShaderNodeMath")
    multiply_node.location.x = x_pos + x_diff * 6
    multiply_node.location.y = y_pos
    multiply_node.inputs[1].default_value = strength
    multiply_node.operation = "MULTIPLY"
    links.new(overlay.outputs["Color"], multiply_node.inputs[0])

    # add texture coords to make the scaling of the dust texture possible
    texture_coords = nodes.new("ShaderNodeTexCoord")
    texture_coords.location.x = x_pos + x_diff * 0
    texture_coords.location.y = y_pos - y_diff * 2
    mapping_node = nodes.new("ShaderNodeMapping")
    mapping_node.location.x = x_pos + x_diff * 1
    mapping_node.location.y = y_pos - y_diff * 2
    mapping_node.vector_type = "TEXTURE"
    scale_value = texture_scale
    mapping_node.inputs["Scale"].default_value = [scale_value] * 3
    links.new(texture_coords.outputs["UV"], mapping_node.inputs["Vector"])
    # check if a texture should be used
    if texture_nodes is not None and texture_nodes:
        texture_node = nodes.new("ShaderNodeTexImage")
        texture_node.location.x = x_pos + x_diff * 2
        texture_node.location.y = y_pos - y_diff * 2
        texture_node.image = random.choice(texture_nodes).image
        links.new(mapping_node.outputs["Vector"], texture_node.inputs["Vector"])
        links.new(texture_node.outputs["Color"], overlay.inputs["Color2"])
    else:
        if not texture_nodes:
            warnings.warn("No texture was found, check the config. Random generated texture is used.")
        # if no texture is used, we great a random noise pattern, which is used instead
        noise_node = nodes.new("ShaderNodeTexNoise")
        noise_node.location.x = x_pos + x_diff * 2
        noise_node.location.y = y_pos - y_diff * 2
        # this determines the pattern of the dust flakes, a high scale makes them small enough to look like dust
        noise_node.inputs["Scale"].default_value = 250.0
        noise_node.inputs["Detail"].default_value = 0.0
        noise_node.inputs["Roughness"].default_value = 0.0
        noise_node.inputs["Distortion"].default_value = 1.9
        links.new(mapping_node.outputs["Vector"], noise_node.inputs["Vector"])
        # this noise_node produces RGB colors, we only need one value in this instance red
        separate_r_channel = nodes.new("ShaderNodeSeparateRGB")
        separate_r_channel.location.x = x_pos + x_diff * 3
        separate_r_channel.location.y = y_pos - y_diff * 2
        links.new(noise_node.outputs["Color"], separate_r_channel.inputs["Image"])
        # as the produced noise image has a nice fading to it, we use a color ramp to create dust flakes
        color_ramp = nodes.new("ShaderNodeValToRGB")
        color_ramp.location.x = x_pos + x_diff * 4
        color_ramp.location.y = y_pos - y_diff * 2
        color_ramp.color_ramp.elements[0].position = 0.4
        color_ramp.color_ramp.elements[0].color = [1, 1, 1, 1]
        color_ramp.color_ramp.elements[1].position = 0.46
        color_ramp.color_ramp.elements[1].color = [0, 0, 0, 1]
        links.new(separate_r_channel.outputs["R"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], overlay.inputs["Color2"])

    # combine the previous color with the new dust mode
    mix_shader = nodes.new("ShaderNodeMixShader")
    mix_shader.location = (x_pos + x_diff * 8, y_pos)
    links.new(multiply_node.outputs["Value"], mix_shader.inputs["Fac"])

    # add a bsdf node for the dust, this will be used to actually give the dust a color
    dust_color = nodes.new("ShaderNodeBsdfPrincipled")
    dust_color.location = (x_pos + x_diff * 6, y_pos - y_diff)
    # the used dust color is a grey with a tint in orange
    dust_color.inputs["Base Color"].default_value = [0.8, 0.773, 0.7, 1.0]
    dust_color.inputs["Roughness"].default_value = 1.0
    dust_color.inputs["Specular"].default_value = 0.0
    links.new(dust_color.outputs["BSDF"], mix_shader.inputs[2])

    # create the input and output nodes inside of the group
    group_output = nodes.new("NodeGroupOutput")
    group_output.location = (x_pos + x_diff * 9, y_pos)
    group_input = nodes.new("NodeGroupInput")
    group_input.location = (x_pos + x_diff * 7, y_pos - y_diff * 0.5)

    # create sockets for the outside of the group match them to the mix shader
    group.outputs.new(mix_shader.outputs[0].bl_idname, mix_shader.outputs[0].name)
    group.inputs.new(mix_shader.inputs[1].bl_idname, mix_shader.inputs[1].name)
    group.inputs.new(multiply_node.inputs[1].bl_idname, "Dust strength")
    group.inputs.new(mapping_node.inputs["Scale"].bl_idname, "Texture scale")

    # link the input and output to the mix shader
    links.new(group_input.outputs[0], mix_shader.inputs[1])
    links.new(mix_shader.outputs[0], group_output.inputs[0])
    links.new(group_input.outputs["Dust strength"], multiply_node.inputs[1])
    links.new(group_input.outputs["Texture scale"], mapping_node.inputs["Scale"])

    # remove the connection between the output and the last node and put the mix shader in between
    node_connected_to_the_output, material_output = material.get_node_connected_to_the_output_and_unlink_it()

    # place the group node above the material output
    group_node.location = (material_output.location.x - x_diff, material_output.location.y + y_diff)

    # connect the dust group
    material.link(node_connected_to_the_output.outputs[0], group_node.inputs[0])
    material.link(group_node.outputs[0], material_output.inputs["Surface"])

    # set the default values
    group_node.inputs["Dust strength"].default_value = strength
    group_node.inputs["Texture scale"].default_value = [texture_scale] * 3
