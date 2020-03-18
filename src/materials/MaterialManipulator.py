import bpy
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
       "selector" "To select the desired materials, should use getter.Material (provider). Type: List of materials"
       "mode" "There are two modes for setting attribute values, can be either 'once_for_each' or 'once_for_all', default: 'once_for_each'"
       "color_link_to_displacement" "Links the output of the texture image to the displacement, the factor determines the strength of the displacement. Type: float"
       "change_to_vertex_color" "Changes the material to a vertex coloring mode, the value should be the name of the vertex color layer. Type: string"
    """

    def __init__(self, config):
        Module.__init__(self, config)

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
        for key in params_conf.data.keys():
            result = None
            if op_mode == "once_for_all":
                # get raw value from the set parameters if it is to be sampled anew for each selected entity
                result = params_conf.get_raw_value(key)

            for material in materials:
                if not material.use_nodes:
                    raise Exception("This material does not use nodes -> not supported here.")

                if op_mode == "once_for_each":
                    # get raw value from the set parameters if it is to be sampled anew for each selected entity
                    result = params_conf.get_raw_value(key)
                if result is None:
                    raise Exception("This mode is unknown: {}".format(op_mode))
                # if an attribute with such name exists for this entity
                if key == "color_link_to_displacement":
                    MaterialManipulator._link_color_to_displacement_for_mat(material, result)
                elif key == "change_to_vertex_color":
                    MaterialManipulator._map_vertex_color(material, result)
                elif hasattr(material, key):
                    # set the value
                    setattr(material, key, result)

                # TODO exclude global settings to raise exception if attribute not found
                #else:
                #    raise Exception("This attribute: {} is not there!".format(key))

