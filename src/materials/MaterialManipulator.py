import bpy
import os

from src.main.Module import Module
from src.utility.Config import Config
from src.utility.Utility import Utility


class MaterialManipulator(Module):
    """
    This class can manipulate materials, for now you can set the attribute of a material with it or:
        * link the color of an image to the displacement as seen in the example
        * map the vertex colors of an object to a material
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       "selector" "Materials to be modified (selection via getter.Material Provider). Type: list."
       "mode" "Mode of operation. Available values: 'once_for_each' (sampling the values for each selected material anew), 'once_for_all' (sampling once for all of the selected materials). Optional. Default value: 'once_for_each'. Type: string."
       "color_link_to_displacement" "Factor that determining the strength of the displacement via linking the output of the texture image to the displacement Type: float"
       "change_to_vertex_color" "The name of the vertex color layer, used for changing the material to a vertex coloring mode. Type: string"
       "textures", "Texture data as {texture_type (type of the image/map, i.e. color, roughness, reflection, etc.): texture_path} pairs. Texture_type should be equal to the Shaderinput name in order to be assigned to a ShaderTexImage node that will be linked to this input. Label represents to which shader input this node is aconnected. Type: dict."
       "textures/texture_path", "Path to a texture image. Type: string."
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
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

        if op_mode == "once_for_all":
            # get values to set if they are to be set/sampled once for all selected materials
            params = self._get_the_set_params(params_conf)

        for material in materials:
            if not material.use_nodes:
                raise Exception("This material does not use nodes -> not supported here.")

            if op_mode == "once_for_each":
                # get values to set if they are to be set/sampled anew for each selected entity
                params = self._get_the_set_params(params_conf)

            for key, value in params.iteritems():
                # if an attribute with such name exists for this entity
                if key == "color_link_to_displacement":
                    MaterialManipulator._link_color_to_displacement_for_mat(material, value)
                elif key == "change_to_vertex_color":
                    MaterialManipulator._map_vertex_color(material, value)
                elif key == "textures":
                    loaded_textures = self._load_textures(value)
                    self._set_textures(loaded_textures, material)
                elif hasattr(material, key):
                    # set the value
                    setattr(material, key, value)

                # TODO exclude global settings to raise exception if attribute not found
                #else:
                #    raise Exception("This attribute: {} is not there!".format(key))

    def _get_the_set_params(self, params_conf):
        """ Extracts actual values to set from a Config object.

        :param params_conf: Object with all user-defined data. Type: Config.
        :return: Parameters to set as {name of the parameter: it's value} pairs. Type: dict.
        """
        params = {}
        for key in params_conf.data.keys():
            result = None
            if key == "color_link_to_displacement":
                result = params_conf.get_float(key)
            elif key == "change_to_vertex_color":
                result = params_conf.get_string(key)
            elif key == "textures":
                result = {}
                paths_conf = Config(params_conf.get_raw_dict(key))
                for text_key in paths_conf.data.keys():
                    text_path = paths_conf.get_string(text_key)
                    result.update({text_key: text_path})
            else:
                result = params_conf.get_raw_value(key)

            params.update({key: result})

        return params

    def _load_textures(self, text_paths):
        """ Loads textures.

        :param text_paths: Texture data as {texture type (image/map type, i.e. color, roughness, reflection, etc.): texture path} pairs. Type: dict.
        :return: Loaded texture data as {texture type (image/map type, i.e. color, roughness, reflection, etc.): texture object} pairs. Type: dict.
        """
        loaded_textures = {}
        for key in text_paths.keys():
            bpy.ops.image.open(filepath=text_paths[key], directory=os.path.dirname(text_paths[key]))
            loaded_textures.update({key: bpy.data.images.get(os.path.basename(text_paths[key]))})

        return loaded_textures

    def _set_textures(self, loaded_textures, material):
        """ Creates a ShaderNodeTexImage node, assigns a loaded image to it and connects to the shader of the selected materials.

        :param loaded_textures: Loaded texture data as {texture type: texture object} pairs. Type: dict.
        :param material: Material to be modified. Type: bpy.material.
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
    def _link_color_to_displacement_for_mat(material, multiply_factor):
        """
        Link the output of the one texture image to the displacement

        Fails if there is more than one texture image

        :param material input material, which will be changed
        :param multiply_factor the factor with which the displacement is multiplied
        """
        nodes = material.node_tree.nodes
        output = Utility.get_nodes_with_type(nodes, "OutputMaterial")
        texture = Utility.get_nodes_with_type(nodes, "TexImage")
        if output is not None and texture is not None:
            if len(output) == 1 and len(texture) == 1:
                output = output[0]
                texture = texture[0]

                math_node = nodes.new(type='ShaderNodeMath')
                math_node.operation = "MULTIPLY"
                math_node.inputs[1].default_value = multiply_factor
                material.node_tree.links.new(texture.outputs["Color"], math_node.inputs[0])
                material.node_tree.links.new(math_node.outputs["Value"], output.inputs["Displacement"])
            else:
                raise Exception("The amount of output nodes and texture nodes does not work with the option.")

    @staticmethod
    def _map_vertex_color(material, layer_name):
        """
        Replace the material with a mapping of the vertex color to a background color node.
            These nodes are unable to be effected by light or shadow.
        :param material the material which should be changed
        :param layer_name the name of the vertex color layer
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
            raise Exception("The material: {} has no node connected to the output, "
                            "which has as an input Base Color".format(material.name))
