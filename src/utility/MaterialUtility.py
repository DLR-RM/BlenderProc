import bpy

from typing import List, Union

from src.utility.StructUtility import Struct
from src.utility.Utility import Utility


class Material(Struct):

    def __init__(self, material: bpy.types.Material):
        super().__init__(material)
        if not material.use_nodes:
            raise Exception("The given material " + material.name + " does not have nodes enabled and can therefore not be handled by BlenderProc's Material wrapper class.")

        self.nodes = material.node_tree.nodes
        self.links = material.node_tree.links

    @staticmethod
    def create(name: str) -> "Material":
        """ Creates a new empty material.

        :param name: The name of the new material.
        :return: The new material.
        """
        new_mat = bpy.data.materials.new(name=name)
        new_mat.use_nodes = True
        return Material(new_mat)

    @staticmethod
    def convert_to_materials(blender_materials: list) -> List["Material"]:
        """ Converts the given list of blender materials to materials

        :param blender_materials: List of materials.
        :return: The list of materials.
        """
        return [(None if obj is None else Material(obj)) for obj in blender_materials]

    def get_users(self) -> int:
        """ Returns the number of users of the material.

        :return: The number of users.
        """
        return self.blender_obj.users

    def duplicate(self) -> "Material":
        """ Duplicates the material.

        :return: The new material which is a copy of this one.
        """
        return Material(self.blender_obj.copy())

    def get_the_one_node_with_type(self, node_type: str) -> bpy.types.Node:
        """ Returns the one node which is of the given node_type

        This function will only work if there is only one of the nodes of this type.

        :param node_type: The node type to look for.
        :return: The node.
        """
        return Utility.get_the_one_node_with_type(self.nodes, node_type)

    def get_nodes_with_type(self, node_type: str) -> [bpy.types.Node]:
        """ Returns all nodes which are of the given node_type

        :param node_type: The note type to look for.
        :return: The list of nodes with the given type.
        """
        return Utility.get_nodes_with_type(self.nodes, node_type)

    def new_node(self, node_type: str) -> bpy.types.Node:
        """ Creates a new node in the material's node tree.

        :param node_type: The desired type of the new node.
        :return: The new node.
        """
        return self.nodes.new(node_type)

    def remove_node(self, node: bpy.types.Node):
        """ Removes the node from the material's node tree.

        :param node: The node to remove.
        """
        self.nodes.remove(node)

    def insert_node_instead_existing_link(self, source_socket: bpy.types.NodeSocket,
                                          new_node_dest_socket: bpy.types.NodeSocket,
                                          new_node_src_socket: bpy.types.NodeSocket,
                                          dest_socket: bpy.types.NodeSocket):
        """ Replaces the node between source_socket and dest_socket with a new node.

        Before: source_socket -> dest_socket
        After: source_socket -> new_node_dest_socket and new_node_src_socket -> dest_socket

        :param source_socket: The source socket.
        :param new_node_dest_socket: The new destination for the link starting from source_socket.
        :param new_node_src_socket: The new source for the link towards dest_socket.
        :param dest_socket: The destination socket
        """
        Utility.insert_node_instead_existing_link(self.links, source_socket, new_node_dest_socket, new_node_src_socket,
                                                  dest_socket)

    def link(self, source_socket: bpy.types.NodeSocket, dest_socket: bpy.types.NodeSocket):
        """ Creates a new link between the two given sockets.

        :param source_socket: The source socket.
        :param dest_socket: The destination socket
        """
        self.links.new(source_socket, dest_socket)

    def unlink(self, source_socket: bpy.types.NodeSocket, dest_socket: bpy.types.NodeSocket):
        """ Removes the link between the two given sockets.

        :param source_socket: The source socket.
        :param dest_socket: The destination socket
        """
        self.links.remove(source_socket, dest_socket)

    def map_vertex_color(self, layer_name: str):
        """ Replaces the material with a mapping of the vertex color to a background color node.

        :param layer_name: Name of the vertex color layer. Type: string.
        """
        # create new vertex color shade node
        vcol = self.nodes.new(type="ShaderNodeVertexColor")
        vcol.layer_name = layer_name
        node_connected_to_output, material_output = Utility.get_node_connected_to_the_output_and_unlink_it(self.blender_obj)
        self.nodes.remove(node_connected_to_output)
        background_color_node = self.nodes.new(type="ShaderNodeBackground")
        if 'Color' in background_color_node.inputs:
            self.links.new(vcol.outputs['Color'], background_color_node.inputs['Color'])
            self.links.new(background_color_node.outputs["Background"], material_output.inputs["Surface"])
        else:
            raise Exception("Material '{}' has no node connected to the output, "
                            "which has as a 'Base Color' input.".format(self.blender_obj.name))

    def make_emissive(self, emission_strength: float, replace: bool = False, keep_using_base_color: bool = True,
                      emission_color: list = None, non_emissive_color_socket: bpy.types.NodeSocket = None):
        """ Makes the material emit light.

        :param emission_strength: The strength of the emitted light.
        :param replace: When replace is set to True, the existing material will be completely replaced by the emission shader, otherwise it still looks the same, while emitting light.
        :param keep_using_base_color: If True, the base color of the material will be used as emission color.
        :param emission_color: The color of the light to emit. Is ignored if keep_using_base_color is set to True.
        :param non_emissive_color_socket: An output socket that defines how the material should look like. By default that is the output of the principled shader node. Has no effect if replace is set to True.
        """
        output_node = self.get_the_one_node_with_type("OutputMaterial")

        if not replace:
            mix_node = self.new_node('ShaderNodeMixShader')
            if non_emissive_color_socket is None:
                principled_bsdf = self.get_the_one_node_with_type("BsdfPrincipled")
                non_emissive_color_socket = principled_bsdf.outputs['BSDF']
            self.insert_node_instead_existing_link(non_emissive_color_socket, mix_node.inputs[2],
                                                   mix_node.outputs['Shader'], output_node.inputs['Surface'])

            # The light path node returns 1, if the material is hit by a ray coming from the camera, else it
            # returns 0. In this way the mix shader will use the principled shader for rendering the color of
            # the emitting surface itself, while using the emission shader for lighting the scene.
            light_path_node = self.new_node('ShaderNodeLightPath')
            self.link(light_path_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])
            output_socket = mix_node.inputs[1]
        else:
            output_socket = output_node.inputs['Surface']

        emission_node = self.new_node('ShaderNodeEmission')

        if keep_using_base_color:
            principled_bsdf = self.get_the_one_node_with_type("BsdfPrincipled")
            if len(principled_bsdf.inputs["Base Color"].links) == 1:
                # get the node connected to the Base Color
                socket_connected_to_the_base_color = principled_bsdf.inputs["Base Color"].links[0].from_socket
                self.link(socket_connected_to_the_base_color, emission_node.inputs["Color"])
            else:
                emission_node.inputs["Color"].default_value = principled_bsdf.inputs["Base Color"].default_value
        elif emission_color is not None:
            emission_node.inputs["Color"].default_value = emission_color

        # set the emission strength of the shader
        emission_node.inputs['Strength'].default_value = emission_strength

        self.link(emission_node.outputs["Emission"], output_socket)

    def set_principled_shader_value(self, input_name: str, value: Union[float, bpy.types.Image, bpy.types.NodeSocket]):
        """ Sets value of an input to the principled shader node.

        :param input_name: The name of the input socket of the principled shader node.
        :param value: The value to set. Can be a simple value to use as default_value, a socket which will be connected to the input or an image which will be used for a new TextureNode connected to the input.
        """
        principled_bsdf = self.get_the_one_node_with_type("BsdfPrincipled")

        if isinstance(value, bpy.types.Image):
            node = self.new_node('ShaderNodeTexImage')
            node.label = input_name
            node.image = value
            self.link(node.outputs['Color'], principled_bsdf.inputs[input_name])
        elif isinstance(value, bpy.types.NodeSocket):
            self.link(value, principled_bsdf.inputs[input_name])
        else:
            principled_bsdf.inputs[input_name].default_value = value

    def get_principled_shader_value(self, input_name: str) -> Union[float, bpy.types.Node]:
        """ Gets the default value or the connected node to an input socket of the principled shader node of the material.

        :param input_name: The name of the input socket of the principled shader node.
        :return: the connected node to the input socket or the default_value of the given input_name
        """
        # get the one node from type Principled BSDF
        principled_bsdf = self.get_the_one_node_with_type("BsdfPrincipled")
        # check if the input name is a valid input
        if input_name in principled_bsdf.inputs:
            # check if there are any connections to this input socket
            if principled_bsdf.inputs[input_name].links:
                if len(principled_bsdf.inputs[input_name].links) == 1:
                    # return the connected node
                    return principled_bsdf.inputs[input_name].links[0].from_node
                else:
                    raise Exception(f"The input socket has more than one input link: "
                                    f"{[link.from_node.name for link in principled_bsdf.inputs[input_name].links]}")
            else:
                # else return the default value
                return principled_bsdf.inputs[input_name].default_value
        else:
            raise Exception(f"The input name could not be found in the inputs: {input_name}")

    def get_node_connected_to_the_output_and_unlink_it(self):
        """
        Searches for the OutputMaterial in the material and finds the connected node to it,
        removes the connection between this node and the output and returns this node and the material_output
        """
        material_output = self.get_the_one_node_with_type('OutputMaterial')
        # find the node, which is connected to the output
        node_connected_to_the_output = None
        for link in self.links:
            if link.to_node == material_output:
                node_connected_to_the_output = link.from_node
                # remove this link
                self.links.remove(link)
                break
        return node_connected_to_the_output, material_output

    def __setattr__(self, key, value):
        if key not in ["links", "nodes", "blender_obj"]:
            raise Exception("The API class does not allow setting any attribute. Use the corresponding method or directly access the blender attribute via entity.blender_obj.attribute_name")
        else:
            object.__setattr__(self, key, value)
