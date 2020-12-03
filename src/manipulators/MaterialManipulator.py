import os
import warnings

import bpy

from src.main.Module import Module
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

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "selector", "Materials to become subjects of manipulation. Type: Provider."
        "mode", "Mode of operation. Type: string. Default: "once_for_each". Available: 'once_for_each' (if samplers are "
               "called, new sampled value is set to each selected material), 'once_for_all' (sampling once for all "
               "of the selected materials)."

    **Values to set**:

    .. csv-table::
        :header: "Parameter", "Description"

        "key", "Name of the attribute to change or a name of a custom function to perform on materials. "
               "Type: string. "
               "In order to specify, what exactly one wants to modify (e.g. attribute, custom property, etc.): "
               "For attribute: key of the pair must be a valid attribute name of the selected material. "
               "For calling custom function: key of the pair must start with `cf_` prefix. See table below for "
               "supported custom function names."
        "value", "Value of the attribute/custom prop. to set or input value(s) for a custom function. Type: string, "
                 "int, bool or float, list/Vector."

    **Available custom functions**:

    .. csv-table::
        :header: "Parameter", "Description"

        "cf_color_link_to_displacement", "Factor that determines the strength of the displacement via linking the "
                                        "output of the texture image to the displacement Type: float"
        "cf_change_to_vertex_color", "The name of the vertex color layer, used for changing the material to a vertex "
                                    "coloring mode. Type: string"
        "cf_textures", "Texture data as {texture_type (type of the image/map, i.e. color, roughness, reflection, etc.): "
                       "texture_path} pairs. Texture_type should be equal to the Shader input name in order to be "
                       "assigned to a ShaderTexImage node that will be linked to this input. Label represents to which "
                       "shader input this node is connected. Type: dict."
        "cf_textures/texture_path", "Path to a texture image. Type: string."
        "cf_switch_to_emission_shader", "Adds the Emission shader to the target material, sets it's 'color' and "
                                        "'strength' values, connects it to the Material Output node. Type: dict."
        "cf_switch_to_emission_shader/color", "[R, G, B, A] vector representing the color of the emitted light. "
                                              "Type: mathutils.Vector."
        "cf_switch_to_emission_shader/strength", "Strength of the emitted light. Must be >0. Type: float."
        "cf_set_*", "Sets value to the * (suffix) input of the Principled BSDF shader. Replace * with all lower-case "
                    "name of the input (use '_' if those are represented by multiple nodes, e.g. 'Base Color' -> "
                    "'base_color'). Also deletes any links to this shader's input point. Type: int, float, list, Vector."
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
                elif "set_" in key_copy and requested_cf:
                    # sets the value of the principled shader
                    self._set_principled_shader_value(material, key_copy[len("set_"):], value)
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
            elif "cf_set_" in key:
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
    def _set_principled_shader_value(material, shader_input_key, value):
        """

        :param material: Material to be modified. Type: bpy.types.Material.
        :param shader_input_key: Name of the shader's input. Type: string.
        :param value: Value to set.
        """
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
        shader_input_key_copy = shader_input_key.replace("_", " ").title()
        if principled_bsdf.inputs[shader_input_key_copy].links:
            links.remove(principled_bsdf.inputs[shader_input_key_copy].links[0])
        if shader_input_key_copy in principled_bsdf.inputs:
            principled_bsdf.inputs[shader_input_key_copy].default_value = value
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
