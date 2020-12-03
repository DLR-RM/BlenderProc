
from src.main.Module import Module
from src.utility.Config import Config
from src.utility.Utility import Utility


class SceneNetLighting(Module):
    """
    Adds lighting to the scene, by adding emission shader nodes to lamps and the ceiling so that each
    scene is well illuminated.

    This is even true if the original material is not there anymore. As we change the materials based on the name
    of the objects. These objects will be selected via the custom property "is_scene_net_obj".

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - lampshade_emission_strength
          - The strength of the lamp emission shader. efault: 15
          - float 
        * - ceiling_emission_strength
          - The strength of the ceiling emission shader. efault: 2
          - float 
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        own_config = Config({"selector": {"provider": "getter.Entity",
                      "conditions": {
                          "cp_is_scene_net_obj": True
                      }}})
        # get all objects which have the custom property is_scene_net_obj: True
        objects = own_config.get_list("selector")
        if not objects:
            raise Exception("No objects have been loaded which have the custom property is_scene_net_obj!")
        self.add_emission_to_materials(objects)

    def add_emission_to_materials(self, objects):
        """
        Add emission shader to the materials of the objects which are named either lamp or ceiling

        This will even work if the original materials have been replaced
        :param objects, to change the materials of
        """
        # for each object add a material
        for obj in objects:
            for mat_slot in obj.material_slots:
                obj_name = obj.name
                if "." in obj_name:
                    obj_name = obj_name[:obj_name.find(".")]
                obj_name = obj_name.replace("_", "").lower()
                # remove all digits from the string
                obj_name = ''.join([i for i in obj_name if not i.isdigit()])
                if "lamp" in obj_name or "ceiling" in obj_name:

                    material = mat_slot.material
                    # if there is more than one user make a copy and then use the new one
                    if material.users > 1:
                        new_mat = material.copy()
                        mat_slot.material = new_mat
                        material = mat_slot.material
                    # rename the material
                    material.name += "_emission"

                    nodes = material.node_tree.nodes
                    links = material.node_tree.links
                    principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                    output_node = Utility.get_the_one_node_with_type(nodes, "OutputMaterial")

                    mix_node = nodes.new(type='ShaderNodeMixShader')
                    Utility.insert_node_instead_existing_link(links, principled_bsdf.outputs['BSDF'], mix_node.inputs[2],
                                                              mix_node.outputs['Shader'], output_node.inputs['Surface'])

                    # The light path node returns 1, if the material is hit by a ray coming from the camera, else it returns 0.
                    # In this way the mix shader will use the principled shader for rendering the color of the lightbulb itself, while using the emission shader for lighting the scene.
                    lightPath_node = nodes.new(type='ShaderNodeLightPath')
                    links.new(lightPath_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                    emission_node = nodes.new(type='ShaderNodeEmission')
                    if "lamp" in obj_name:
                        if len(principled_bsdf.inputs["Base Color"].links) == 1:
                            # get the node connected to the Base Color
                            node_connected_to_the_base_color = principled_bsdf.inputs["Base Color"].links[0].from_node
                            # use 0 as it is probably the first one
                            links.new(node_connected_to_the_base_color.outputs[0], emission_node.inputs["Color"])

                        # If the material corresponds to a lampshade
                        emission_node.inputs['Strength'].default_value = \
                            self.config.get_float("lampshade_emission_strength", 15)
                    elif "ceiling" in obj_name:
                        # If the material corresponds to a ceiling
                        emission_node.inputs['Strength'].default_value = self.config.get_float("ceiling_emission_strength", 2)

                    links.new(emission_node.outputs["Emission"], mix_node.inputs[1])




