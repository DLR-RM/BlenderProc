import bpy
import mathutils

from src.main.Module import Module
from src.utility.Config import Config
from src.utility.Utility import Utility


class SurfaceLighting(Module):
    """
    Adds lighting to the scene, by adding emission shader nodes to surfaces of specified objects.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - selection
          - Selection of objects, via the `getter.Entity`.
        * - emission_strength
          - The strength of the emission shader. Default: 10.0.
          - float
        * - keep_using_base_color
          - If this is True, the Base Color of the material is kept, this means if the material was yellow before. \
            The light now is also yellow. Default: False.
          - bool
        * - emission_color
          - If `keep_using_case_color` is False it is possible to set the color of the light with an RGB value. All \
            values have to be in the range from [0, 1]. Default: None.
          - mathutils.Vector
    """

    def __init__(self, config: Config):
        Module.__init__(self, config)
        self.emission_strength = self.config.get_float("emission_strength", 10.0)
        self.keep_using_base_color = self.config.get_bool("keep_using_base_color", False)
        self.emission_color = None
        if self.config.has_param("emission_color"):
            self.emission_color = self.config.get_vector3d("emission_color")

    def run(self):
        """
        Run this current module.
        """
        # get all objects which material should be changed
        objects = self.config.get_list("selector")

        self.add_emission_to_materials(objects)

    def add_emission_to_materials(self, objects):
        """
        Add emission shader to the materials of the objects which are selected via the `selector`

        :param objects: to change the materials of
        """
        # for each object add a material
        for obj in objects:
            if len(obj.material_slots) == 0:
                # this object has no material so far -> create one
                new_mat = bpy.data.materials.new(name="TextureLess")
                new_mat.use_nodes = True
                obj.data.materials.append(new_mat)

            for mat_slot in obj.material_slots:

                material = mat_slot.material
                # if there is more than one user make a copy and then use the new one
                if material.users > 1:
                    new_mat = material.copy()
                    mat_slot.material = new_mat
                    material = mat_slot.material
                # rename the material
                material.name += "_emission"
                # add a custom property to later identify these materials
                material["is_lamp"] = True

                # access the nodes and links of the material
                nodes, links = material.node_tree.nodes, material.node_tree.links
                principled_bsdfs = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
                if len(principled_bsdfs) == 1:
                    principled_bsdf = principled_bsdfs[0]
                else:
                    raise Exception("This only works if there is only one Bsdf Principled Node in the material: "
                                    "{}".format(material.name))
                output_node = Utility.get_the_one_node_with_type(nodes, "OutputMaterial")

                mix_node = nodes.new(type='ShaderNodeMixShader')
                Utility.insert_node_instead_existing_link(links, principled_bsdf.outputs['BSDF'], mix_node.inputs[2],
                                                          mix_node.outputs['Shader'], output_node.inputs['Surface'])

                # The light path node returns 1, if the material is hit by a ray coming from the camera, else it
                # returns 0. In this way the mix shader will use the principled shader for rendering the color of
                # the emitting surface itself, while using the emission shader for lighting the scene.
                light_path_node = nodes.new(type='ShaderNodeLightPath')
                links.new(light_path_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                emission_node = nodes.new(type='ShaderNodeEmission')

                if self.keep_using_base_color:
                    if len(principled_bsdf.inputs["Base Color"].links) == 1:
                        # get the node connected to the Base Color
                        node_connected_to_the_base_color = principled_bsdf.inputs["Base Color"].links[0].from_node
                        # use 0 as it is probably the first one
                        links.new(node_connected_to_the_base_color.outputs[0], emission_node.inputs["Color"])
                elif self.emission_color is not None:
                    emission_node.inputs["Color"] = self.emission_color

                # set the emission strength of the shader
                emission_node.inputs['Strength'].default_value = self.emission_strength

                links.new(emission_node.outputs["Emission"], mix_node.inputs[1])




