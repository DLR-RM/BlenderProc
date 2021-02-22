import os
import random
import warnings

import bpy
import mathutils

from src.main.Module import Module
from src.utility import BlenderUtility
from src.utility.Config import Config
from src.utility.Utility import Utility


class MaterialManipulator(Module):
    """
    Performs manipulation os selected materials.

    Example 1: Link image texture output of the 'Material.001' material to displacement input of the shader with a
               strength factor of 1.5.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config": {
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": "Material.001"
              }
            },
            "cf_color_link_to_displacement": 1.5
          }
        }

    Example 2: Set base color of all materials matching the name pattern to white.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config": {
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": ".*material.*"
              }
            },
            "cf_set_base_color": [1, 1, 1, 1]
          }
        }

    Example 3: For all materials matching the name pattern switch to the Emission shader with emitted light of red
    color of energy 15.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config": {
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": ".*material.*"
              }
            },
            "cf_switch_to_emission_shader": {
              "color": [1, 0, 0, 1],
              "strength": 15
            }
          }
        }

    Example 4: Add a layer of dust to all materials. By using a random generated dust texture. The strength here
    determines how thick the dust layer is. The texture scale determines the size of the dust flakes. At one it gets
    the same as the normal texture on the object. Be aware that each object needs a UV map so that the dust flakes
    are properly displayed.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config":{
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": ".*",
                "use_nodes": True
              }
            },
            "cf_add_dust": {
              "strength": 0.8,
              "texture_scale": 0.05
            }
          }
        },

    Example 5: Add a layer of dust to all materials. In this example the focus is on loading a texture with the
    TextureLoader and using it with the MaterialManipulator.

    .. code-block:: yaml

        {
          "module": "loader.TextureLoader",
          "config": {
            "path": "<args:0>",
            "add_properties": {
              "cp_dust_texture": True
            }
          }
        },
        {
          "module": "manipulators.MaterialManipulator",
          "config":{
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": ".*",
                "use_nodes": True
              }
            },
            "cf_add_dust": {
              "strength": 0.8,
              "used_dust_texture": {
                "provider": "getter.Texture",
                "conditions": {
                  "cp_dust_texture": True
                }
              },
              "texture_scale": 0.05
            }
          }
        },

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - selector
          - Materials to become subjects of manipulation.
          - Provider
        * - mode
          - Mode of operation. Default: "once_for_each". Available: 'once_for_each' (if samplers are called, new sampled 
            value is set to each selected material), 'once_for_all' (sampling once for all of the selected materials).
          - string

    **Values to set**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - key
          - Name of the attribute to change or a name of a custom function to perform on materials. " In order to
            specify, what exactly one wants to modify (e.g. attribute, custom property, etc.): For attribute: key of
            the pair must be a valid attribute name of the selected material. For calling custom function: key of
            the pair must start with `cf_` prefix. See table below for supported custom function names.
          - string
        * - value
          - Value of the attribute/custom prop. to set or input value(s) for a custom function.
          - string, list/Vector, int, bool or float

    **Available custom functions**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cf_color_link_to_displacement
          - Factor that determines the strength of the displacement via linking the output of the texture image to
            the displacement
          - float
        * - cf_change_to_vertex_color
          - The name of the vertex color layer, used for changing the material to a vertex coloring mode.
          - string
        * - cf_textures
          - Texture data as {texture_type (type of the image/map, i.e. color, roughness, reflection, etc.):
            texture_path} pairs. Texture_type should be equal to the Shader input name in order to be assigned to a
            ShaderTexImage node that will be linked to this input. Label represents to which shader input this node
            is connected. 
          - dict
        * - cf_textures/texture_path
          - Path to a texture image.
          - string
        * - cf_switch_to_emission_shader
          - Adds the Emission shader to the target material, sets it's 'color' and 'strength' values, connects it to
            the Material Output node. 
          - dict
        * - cf_switch_to_emission_shader/color
          - [R, G, B, A] vector representing the color of the emitted light. 
          - mathutils.Vector
        * - cf_switch_to_emission_shader/strength
          - Strength of the emitted light. Must be >0.
          - float
        * - cf_add_dust
          - Adds a layer of dust on all target materials. Dust is always presented on every surface facing upwards
            in Z-direction.
          - dict
        * - cf_add_dust/strength
          - This determines the strength of the dust, 0 means no dust 1.0 means full dust. Values above 1.0 are
            possible, but create a thick film out of dust, which hides the material completely.
          - float
        * - cf_add_dust/used_dust_texture
          - If a specific dust texture should be used, this can be specified. Use a getter.Texture to return a loaded
            texture. If this is empty a random noise texture is generated.
          - getter.Texture
        * - cf_add_dust/texture_scale
          - This scale is used to scale down the used noise texture (even for the case where a random noise texture
            is used). Default: 0.1.
          - float
        * - cf_set_*
          - Sets value to the * (suffix) input of the Principled BSDF shader. Replace * with all lower-case name of
            the input (use '_' if those are represented by multiple nodes, e.g. 'Base Color' -> 'base_color'). Also
            deletes any links to this shader's input point.
          - list/Vector, int or float
        * - cf_add_*
          - Adds value to the * (suffix) input of the Principled BSDF shader. Replace * with all lower-case name of
            the input (use '_' if those are represented by multiple nodes, e.g. 'Base Color' -> 'base_color'). Also
            deletes any links to this shader's input point. The values are not clipped in the end.
          - list/Vector, int or float
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Sets according values of defined attributes or applies custom functions to the selected materials.
            1. Select materials.
            2. For each parameter to modify, set it's value to all selected objects.
        """
        set_params = {}
        sel_objs = {}
        for key in self.config.data.keys():
            # if its not a selector -> to the set parameters dict
            if key != 'selector':
                set_params[key] = self.config.data[key]
            else:
                sel_objs[key] = self.config.data[key]
        # create Config objects
        params_conf = Config(set_params)
        sel_conf = Config(sel_objs)
        # invoke a Getter, get a list of entities to manipulate
        materials = sel_conf.get_list("selector")

        op_mode = self.config.get_string("mode", "once_for_each")

        if not materials:
            warnings.warn("Warning: No materials selected inside of the MaterialManipulator")
            return

        if op_mode == "once_for_all":
            # get values to set if they are to be set/sampled once for all selected materials
            params = self._get_the_set_params(params_conf)

        for material in materials:
            if not material.use_nodes:
                raise Exception("This material does not use nodes -> not supported here.")

            if op_mode == "once_for_each":
                # get values to set if they are to be set/sampled anew for each selected entity
                params = self._get_the_set_params(params_conf)

            for key, value in params.items():

                # used so we don't modify original key when having more than one material
                key_copy = key

                requested_cf = False
                if key.startswith('cf_'):
                    requested_cf = True
                    key_copy = key[3:]

                # if an attribute with such name exists for this entity
                if key_copy == "color_link_to_displacement" and requested_cf:
                    MaterialManipulator._link_color_to_displacement_for_mat(material, value)
                elif key_copy == "change_to_vertex_color" and requested_cf:
                    MaterialManipulator._map_vertex_color(material, value)
                elif key_copy == "textures" and requested_cf:
                    loaded_textures = self._load_textures(value)
                    self._set_textures(loaded_textures, material)
                elif key_copy == "switch_to_emission_shader" and requested_cf:
                    self._switch_to_emission_shader(material, value)
                elif key_copy == "infuse_texture" and requested_cf:
                    MaterialManipulator._infuse_texture(material, value)
                elif key_copy == "infuse_material" and requested_cf:
                    MaterialManipulator._infuse_material(material, value)
                elif key_copy == "add_dust" and requested_cf:
                    self._add_dust_to_material(material, value)
                elif "set_" in key_copy and requested_cf:
                    # sets the value of the principled shader
                    self._op_principled_shader_value(material, key_copy[len("set_"):], value, "set")
                elif "add_" in key_copy and requested_cf:
                    # sets the value of the principled shader
                    self._op_principled_shader_value(material, key_copy[len("add_"):], value, "add")
                elif hasattr(material, key_copy):
                    # set the value
                    setattr(material, key_copy, value)

    def _get_the_set_params(self, params_conf):
        """ Extracts actual values to set from a Config object.

        :param params_conf: Object with all user-defined data. Type: Config.
        :return: Parameters to set as {name of the parameter: it's value} pairs. Type: dict.
        """
        params = {}
        for key in params_conf.data.keys():
            result = None
            if key == "cf_color_link_to_displacement":
                result = params_conf.get_float(key)
            elif key == "cf_change_to_vertex_color":
                result = params_conf.get_string(key)
            elif key == "cf_textures":
                result = {}
                paths_conf = Config(params_conf.get_raw_dict(key))
                for text_key in paths_conf.data.keys():
                    text_path = paths_conf.get_string(text_key)
                    result.update({text_key: text_path})
            elif key == "cf_switch_to_emission_shader":
                result = {}
                emission_conf = Config(params_conf.get_raw_dict(key))
                for emission_key in emission_conf.data.keys():
                    if emission_key == "color":
                        attr_val = emission_conf.get_list("color", [1, 1, 1, 1])
                    elif emission_key == "strength":
                        attr_val = emission_conf.get_float("strength", 1.0)
                    result.update({emission_key: attr_val})
            elif key == "cf_infuse_texture":
                result = Config(params_conf.get_raw_dict(key))
            elif key == "cf_infuse_material":
                result = Config(params_conf.get_raw_dict(key))
            elif key == "cf_add_dust":
                result = params_conf.get_raw_dict(key)
            elif "cf_set_" in key or "cf_add_" in key:
                result = params_conf.get_raw_value(key)
            else:
                result = params_conf.get_raw_value(key)

            params.update({key: result})

        return params

    def _load_textures(self, text_paths):
        """ Loads textures.

        :param text_paths: Texture data. Type: dict.
        :return: Loaded texture data. Type: dict.
        """
        loaded_textures = {}
        for key in text_paths.keys():
            bpy.ops.image.open(filepath=text_paths[key], directory=os.path.dirname(text_paths[key]))
            loaded_textures.update({key: bpy.data.images.get(os.path.basename(text_paths[key]))})

        return loaded_textures

    def _set_textures(self, loaded_textures, material):
        """ Creates a ShaderNodeTexImage node, assigns a loaded image to it and connects it to the shader of the
            selected material.

        :param loaded_textures: Loaded texture data. Type: dict.
        :param material: Material to be modified. Type: bpy.types.Material.
        """
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        # for each Image Texture node set a texture (image) if one was loaded
        for key in loaded_textures.keys():
            node = nodes.new('ShaderNodeTexImage')
            node.label = key
            out_point = node.outputs['Color']
            in_point = nodes["Principled BSDF"].inputs[key]
            node.image = loaded_textures[key]
            links.new(out_point, in_point)

    @staticmethod
    def _op_principled_shader_value(material, shader_input_key, value, operation):
        """
        Sets or adds the given value to the shader_input_key of the principled shader in the material

        :param material: Material to be modified. Type: bpy.types.Material.
        :param shader_input_key: Name of the shader's input. Type: string.
        :param value: Value to set.
        """
        nodes = material.node_tree.nodes
        principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
        shader_input_key_copy = shader_input_key.replace("_", " ").title()
        if principled_bsdf.inputs[shader_input_key_copy].links:
            links = material.node_tree.links
            links.remove(principled_bsdf.inputs[shader_input_key_copy].links[0])
        if shader_input_key_copy in principled_bsdf.inputs:
            if operation == "set":
                principled_bsdf.inputs[shader_input_key_copy].default_value = value
            elif operation == "add":
                if isinstance(principled_bsdf.inputs[shader_input_key_copy].default_value, float):
                    principled_bsdf.inputs[shader_input_key_copy].default_value += value
                else:
                    if len(principled_bsdf.inputs[shader_input_key_copy].default_value) != len(value):
                        raise Exception(f"The shapder input key '{shader_input_key_copy}' needs a value with "
                                        f"{len(principled_bsdf.inputs[shader_input_key_copy].default_value)} "
                                        f"dimensions, the used config value only has {len(value)} dimensions.")
                    for i in range(len(principled_bsdf.inputs[shader_input_key_copy].default_value)):
                        principled_bsdf.inputs[shader_input_key_copy].default_value[i] += value[i]
        else:
            raise Exception("Shader input key '{}' is not a part of the shader.".format(shader_input_key_copy))

    @staticmethod
    def _link_color_to_displacement_for_mat(material, multiply_factor):
        """ Link the output of the texture image to the displacement. Fails if there is more than one texture image.

        :param material: Material to be modified. Type: bpy.types.Material.
        :param multiply_factor: Multiplication factor of the displacement. Type: float.
        """
        nodes = material.node_tree.nodes
        output = Utility.get_the_one_node_with_type(nodes, "OutputMaterial")
        texture = Utility.get_nodes_with_type(nodes, "ShaderNodeTexImage")
        if texture is not None:
            if len(texture) == 1:
                texture = texture[0]
                math_node = nodes.new(type='ShaderNodeMath')
                math_node.operation = "MULTIPLY"
                math_node.inputs[1].default_value = multiply_factor
                material.node_tree.links.new(texture.outputs["Color"], math_node.inputs[0])
                material.node_tree.links.new(math_node.outputs["Value"], output.inputs["Displacement"])
            else:
                raise Exception("The amount of output and texture nodes of the material '{}' is not supported by "
                                "this custom function.".format(material))

    @staticmethod
    def _map_vertex_color(material, layer_name):
        """ Replaces the material with a mapping of the vertex color to a background color node.

        :param material: Material to be modified. Type: bpy.types.Material.
        :param layer_name: Name of the vertex color layer. Type: string.
        """
        nodes = material.node_tree.nodes
        mat_links = material.node_tree.links
        # create new vertex color shade node
        vcol = nodes.new(type="ShaderNodeVertexColor")
        vcol.layer_name = layer_name
        node_connected_to_output, material_output = Utility.get_node_connected_to_the_output_and_unlink_it(material)
        nodes.remove(node_connected_to_output)
        background_color_node = nodes.new(type="ShaderNodeBackground")
        if 'Color' in background_color_node.inputs:
            mat_links.new(vcol.outputs['Color'], background_color_node.inputs['Color'])
            mat_links.new(background_color_node.outputs["Background"], material_output.inputs["Surface"])
        else:
            raise Exception("Material '{}' has no node connected to the output, "
                            "which has as a 'Base Color' input.".format(material.name))

    def _switch_to_emission_shader(self, material, value):
        """ Adds the Emission shader to the target material, sets it's color and strength values, connects it to
            the Material Output node.

        :param material: Material to be modified. Type: bpy.types.Material.
        :param value: Light color and strength data. Type: dict.
        """
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        emission_node = nodes.new("ShaderNodeEmission")
        mat_output = Utility.get_the_one_node_with_type(nodes, "ShaderNodeOutputMaterial")
        emission_node.inputs["Color"].default_value = value["color"]
        emission_node.inputs["Strength"].default_value = value["strength"]
        links.new(emission_node.outputs["Emission"], mat_output.inputs["Surface"])

    @staticmethod
    def _infuse_texture(material: bpy.types.Material, config: Config):
        """
        Overlays the selected material with a texture, this can be either a color texture like for example dirt or
        it can be a texture, which is used as an input to the Principled BSDF of the given material.

        :param material: Material, which will be changed
        :param config: containing the config information
        """
        if not material.use_nodes:
            raise Exception(f"The material {material.name} does not use nodes. Change your selection!")

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        used_mode = config.get_string("mode", "overlay").lower()
        if used_mode not in ["overlay", "mix", "set"]:
            raise Exception(f'This mode is unknown here: {used_mode}, only ["overlay", "mix", "set"]!')

        used_textures = config.get_list("used_texture")
        if len(used_textures) == 0:
            raise Exception(f"You have to select a texture, which is {used_mode} over the material!")

        invert_texture = config.get_bool("invert_texture", False)

        used_texture = random.choice(used_textures)
        used_connector = config.get_string("connection", "Base Color").title()
        texture_scale = config.get_float("texture_scale", 0.05)

        if config.has_param("strength") and used_mode == "set":
            raise Exception("The strength can only be used if the mode is not \"set\"!")
        strength = config.get_float("strength", 0.5)

        principled_bsdfs = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
        if len(principled_bsdfs) != 1:
            raise Exception("This only works with materials, which have exactly one Prinicpled BSDF, "
                            "use a different selector!")
        principled_bsdf = principled_bsdfs[0]
        if used_connector not in principled_bsdf.inputs:
            raise Exception(f"The {used_connector} not an input to Principled BSDF!")

        node_connected_to_the_connector = None
        for link in links:
            if link.to_socket == principled_bsdf.inputs[used_connector]:
                node_connected_to_the_connector = link.from_node
                # remove this connection
                links.remove(link)
        if node_connected_to_the_connector is not None or used_mode == "set":
            texture_node = nodes.new("ShaderNodeTexImage")
            texture_node.image = used_texture.image
            # add texture coords to make the scaling of the dust texture possible
            texture_coords = nodes.new("ShaderNodeTexCoord")
            mapping_node = nodes.new("ShaderNodeMapping")
            mapping_node.vector_type = "TEXTURE"
            mapping_node.inputs["Scale"].default_value = [texture_scale] * 3
            links.new(texture_coords.outputs["UV"], mapping_node.inputs["Vector"])
            links.new(mapping_node.outputs["Vector"], texture_node.inputs["Vector"])
            texture_node_output = texture_node.outputs["Color"]
            if invert_texture:
                invert_node = nodes.new("ShaderNodeInvert")
                invert_node.inputs["Fac"].default_value = 1.0
                links.new(texture_node_output, invert_node.inputs["Color"])
                texture_node_output = invert_node.outputs["Color"]
            if node_connected_to_the_connector is not None and used_mode != "set":
                mix_node = nodes.new("ShaderNodeMixRGB")
                if used_mode in "mix_node":
                    mix_node.blend_type = "OVERLAY"
                elif used_mode in "mix":
                    mix_node.blend_type = "MIX"
                mix_node.inputs["Fac"].default_value = strength
                links.new(texture_node_output, mix_node.inputs["Color2"])
                # hopefully 0 is the color node!
                links.new(node_connected_to_the_connector.outputs[0], mix_node.inputs["Color1"])
                links.new(mix_node.outputs["Color"], principled_bsdf.inputs[used_connector])
            elif used_mode == "set":
                links.new(texture_node_output, principled_bsdf.inputs[used_connector])

    @staticmethod
    def _infuse_material(material: bpy.types.Material, config: Config):
        """

        :param material:
        :param config:
        :return:
        """
        if not material.use_nodes:
            raise Exception(f"The material {material.name} does not use nodes. Change your selection!")

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # determine the mode
        used_mode = config.get_string("mode", "mix").lower()
        if used_mode not in ["add", "mix"]:
            raise Exception(f'This mode is unknown here: {used_mode}, only ["mix", "add"]!')

        if used_mode == "mix":
            mix_strength = config.get_float("mix_strength", 0.5)
        elif used_mode == "add" and config.has_param("mix_strength"):
            raise Exception("The mix_strength only works in the mix mode not in the add mode!")

        used_materials = config.get_list("used_material")
        if len(used_materials) == 0:
            raise Exception(f"You have to select a material, which is {used_mode}ed over the material!")

        used_material = used_materials[0]

        group_node = nodes.new("ShaderNodeGroup")
        group = BlenderUtility.add_nodes_to_group(used_material.node_tree.nodes,
                                                  f"{used_mode.title()}_{used_material.name}")
        group_node.node_tree = group

        material_output = Utility.get_the_one_node_with_type(nodes, "OutputMaterial")
        for mat_output_input in material_output.inputs:
            if len(mat_output_input.links) > 0:
                if "Float" in mat_output_input.bl_idname or "Vector" in mat_output_input.bl_idname:
                    # For displacement
                    infuse_node = nodes.new("ShaderNodeMixRGB")
                    if used_mode in "mix":
                        # as there is no mix mode, we use multiply here, which is similar
                        infuse_node.blend_type = "MULTIPLY"
                        infuse_node.inputs["Fac"].default_value = mix_strength
                        input_offset = 1
                    elif used_mode in "add":
                        infuse_node.blend_type = "ADD"
                        input_offset = 0
                    else:
                        raise Exception(f"This mode is not supported here: {used_mode}!")
                    infuse_output = infuse_node.outputs["Color"]
                else:
                    if used_mode == "mix":
                        infuse_node = nodes.new(type='ShaderNodeMixShader')
                        infuse_node.inputs[0].default_value = mix_strength
                        input_offset = 1
                    elif used_mode == "add":
                        infuse_node = nodes.new(type='ShaderNodeMixShader')
                        input_offset = 0
                    else:
                        raise Exception(f"This mode is not supported here: {used_mode}!")
                    infuse_output = infuse_node.outputs["Shader"]

                for link in input.links:
                    links.new(link.from_socket, infuse_node.inputs[input_offset])
                links.new(group_node.outputs[mat_output_input.name], infuse_node.inputs[input_offset + 1])
                links.new(infuse_output, mat_output_input)

    def _add_dust_to_material(self, material: bpy.types.Material, value: dict):
        """
        Adds a dust film to the material, where the strength determines how much dust is used.

        This will be added right before the output of the material.

        :param material: Used material
        :param value: dict with all used keys
        """

        # extract values from the config, like strength, texture_scale and used_dust_texture
        config = Config(value)
        strength = config.get_float("strength")
        texture_scale = config.get_float("texture_scale", 0.1)
        # if no texture is used, a random noise texture is generated
        texture_nodes = None
        if config.has_param("used_dust_texture"):
            texture_nodes = config.get_list("used_dust_texture")

        group_node = material.node_tree.nodes.new("ShaderNodeGroup")
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
        node_connected_to_the_output, material_output = Utility.get_node_connected_to_the_output_and_unlink_it(material)

        # place the group node above the material output
        group_node.location = (material_output.location.x - x_diff, material_output.location.y + y_diff)

        # connect the dust group
        material.node_tree.links.new(node_connected_to_the_output.outputs[0], group_node.inputs[0])
        material.node_tree.links.new(group_node.outputs[0], material_output.inputs["Surface"])

        # set the default values
        group_node.inputs["Dust strength"].default_value = strength
        group_node.inputs["Texture scale"].default_value = [texture_scale] * 3
