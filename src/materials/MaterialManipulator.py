import bpy
from src.main.Module import Module
from src.utility.Config import Config
from src.utility.Utility import Utility


class MaterialManipulator(Module):

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
        for key in params_conf.data.keys():
            result = None
            if op_mode == "once_for_all":
                # get raw value from the set parameters if it is to be sampled anew for each selected entity
                result = params_conf.get_raw_value(key)

            for material in materials:
                if op_mode == "once_for_each":
                    # get raw value from the set parameters if it is to be sampled anew for each selected entity
                    result = params_conf.get_raw_value(key)
                if result is None:
                    raise Exception("This mode is unknown: {}".format(op_mode))
                # if an attribute with such name exists for this entity
                if key == "color_link_to_displacement":
                    nodes = material.node_tree.nodes
                    output = Utility.get_nodes_with_type(nodes, "OutputMaterial")
                    texture = Utility.get_nodes_with_type(nodes, "TexImage")
                    if output is not None and texture is not None:
                        if len(output) == 1 and len(texture) == 1:
                            output = output[0]
                            texture = texture[0]

                            math_node = nodes.new(type='ShaderNodeMath')
                            math_node.operation = "MULTIPLY"
                            math_node.inputs[1].default_value = result
                            material.node_tree.links.new(texture.outputs["Color"], math_node.inputs[0])
                            material.node_tree.links.new(math_node.outputs["Value"], output.inputs["Displacement"])
                        else:
                            raise Exception("The amount of output nodes and texture nodes does not work with the option.")
                elif hasattr(material, key):
                    # set the value
                    setattr(material, key, result)

                # TODO exclude global settings to raise exception if attribute not found
                #else:
                #    raise Exception("This attribute: {} is not there!".format(key))

