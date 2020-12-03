import csv
import os

import bpy

from src.main.Module import Module
from src.utility.Utility import Utility


class SuncgLighting(Module):
    """ Adds emission shader to lamps, windows and ceilings.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - lightbulb_emission_strength
          - The emission strength that should be used for light bulbs. Default: 15
          - float
        * - lampshade_emission_strength
          - The emission strength that should be used for lamp shades. Default: 7
          - float
        * - ceiling_emission_strength
          - The emission strength that should be used for the ceiling. Default: 1.5
          - float
    """
    def __init__(self, config):
        Module.__init__(self, config)

        # Read in lights
        self.lights = {}
        # File format: <obj id> <number of lightbulb materials> <lightbulb material names> <number of lampshade materials> <lampshade material names>
        with open(Utility.resolve_path(os.path.join('resources', "suncg", "light_geometry_compact.txt"))) as f:
            lines = f.readlines()
            for row in lines:
                row = row.strip().split()
                self.lights[row[0]] = [[], []]

                index = 1

                # Read in lightbulb materials
                number = int(row[index])
                index += 1
                for i in range(number):
                    self.lights[row[0]][0].append(row[index])
                    index += 1

                # Read in lampshade materials
                number = int(row[index])
                index += 1
                for i in range(number):
                    self.lights[row[0]][1].append(row[index])
                    index += 1

        # Read in windows
        self.windows = []
        with open(Utility.resolve_path(os.path.join('resources','suncg','ModelCategoryMapping.csv')), 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["coarse_grained_class"] == "window":
                    self.windows.append(row["model_id"])
        self._collection_of_mats = {"lamp": {}, "window": {}, "ceiling": {}}

    def _make_lamp_emissive(self, obj, light):
        """ Adds an emission shader to the object materials which are specified in the light list

        :param obj: The blender object.
        :param light: A list of two lists. The first list specifies all materials which should act as a lightbulb, the second one lists all materials corresponding to lampshades.
        """
        for m in obj.material_slots:
            mat_name = m.material.name
            if "." in mat_name:
                mat_name = mat_name[:mat_name.find(".")]
            if mat_name in light[0] or mat_name in light[1]:
                old_mat_name = m.material.name
                if old_mat_name in self._collection_of_mats["lamp"]:
                    # this material was used as a ceiling before use that one
                    m.material = self._collection_of_mats["lamp"][old_mat_name]
                    continue
                # copy the material if more than one users is using it
                if m.material.users > 1:
                    new_mat = m.material.copy()
                    m.material = new_mat
                # rename the material
                m.material.name += "_emission"
                nodes = m.material.node_tree.nodes
                links = m.material.node_tree.links

                output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')
                emission = Utility.get_nodes_with_type(nodes, "Emission")
                if not emission:
                    principled = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                    mix_node = nodes.new(type='ShaderNodeMixShader')
                    Utility.insert_node_instead_existing_link(links, principled.outputs['BSDF'], mix_node.inputs[2], mix_node.outputs['Shader'], output.inputs['Surface'])

                    # The light path node returns 1, if the material is hit by a ray coming from the camera, else it returns 0.
                    # In this way the mix shader will use the principled shader for rendering the color of the lightbulb itself, while using the emission shader for lighting the scene.
                    lightPath_node = nodes.new(type='ShaderNodeLightPath')
                    links.new(lightPath_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                    emission_node = nodes.new(type='ShaderNodeEmission')
                    emission_node.inputs['Color'].default_value = m.material.diffuse_color

                    if mat_name in light[0]:
                        # If the material corresponds to light bulb
                        emission_node.inputs['Strength'].default_value = self.config.get_float("lightbulb_emission_strength", 15)
                    else:
                        # If the material corresponds to a lampshade
                        emission_node.inputs['Strength'].default_value = self.config.get_float("lampshade_emission_strength", 7)

                    links.new(emission_node.outputs["Emission"], mix_node.inputs[1])
                    self._collection_of_mats["lamp"][old_mat_name] = m.material

    def _make_window_emissive(self, obj):
        """ Makes the given window object emissive.

        For each material with alpha < 1.
        Uses a light path node to make it emit light, but at the same time look like a principle material.
        Otherwise windows would be completely white.

        :param obj: A window object.
        """
        for m in obj.material_slots:
            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links

            # All parameters imported from the .mtl file are stored inside the principled bsdf node
            principled_node = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
            alpha = principled_node.inputs['Alpha'].default_value

            if alpha < 1:
                mat_name = m.material.name
                if mat_name in self._collection_of_mats["window"]:
                    # this material was used as a ceiling before use that one
                    m.material = self._collection_of_mats["window"][mat_name]
                    continue
                # copy the material if more than one users is using it
                if m.material.users > 1:
                    new_mat = m.material.copy()
                    m.material = new_mat
                    nodes = m.material.node_tree.nodes
                    links = m.material.node_tree.links
                # rename the material
                m.material.name += "_emission"
                emission = Utility.get_nodes_with_type(nodes, 'Emission')
                if not emission:
                    output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')
                    link = next(l for l in links if l.to_socket == output.inputs['Surface'])
                    links.remove(link)

                    # The light path node returns 1, if the material is hit by a ray coming from the camera, else it returns 0.
                    # In this way the mix shader will use the diffuse shader for rendering the color of the window itself, while using the emission shader for lighting the scene.
                    mix_node = nodes.new(type='ShaderNodeMixShader')
                    emission_node = nodes.new(type='ShaderNodeEmission')
                    transparent_node = nodes.new(type='ShaderNodeBsdfDiffuse')
                    transparent_node.inputs['Color'].default_value[:3] = (0.285, 0.5, 0.48)
                    lightPath_node = nodes.new(type='ShaderNodeLightPath')

                    links.new(mix_node.outputs["Shader"], output.inputs['Surface'])
                    links.new(lightPath_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])
                    links.new(emission_node.outputs['Emission'], mix_node.inputs[1])
                    links.new(transparent_node.outputs['BSDF'], mix_node.inputs[2])

                    emission_node.inputs['Color'].default_value = (1, 1, 1, 1)
                    emission_node.inputs['Strength'].default_value = 10  # strength of the windows
                    self._collection_of_mats["window"][mat_name] = m.material
                else:
                    self._collection_of_mats["window"][mat_name] = m.material

    def _make_ceiling_emissive(self, obj):
        """ Makes the given ceiling object emissive, s.t. there is always a little bit ambient light.

        :param obj: The ceiling object.
        """
        for m in obj.material_slots:
            mat_name = m.material.name
            if mat_name in self._collection_of_mats["ceiling"]:
                # this material was used as a ceiling before use that one
                m.material = self._collection_of_mats["ceiling"][mat_name]
                continue
            # copy the material if more than one users is using it
            if m.material.users > 1:
                new_mat = m.material.copy()
                m.material = new_mat
            # rename the material
            if "." in m.material.name:
                # remove everything after the dot
                m.material.name = m.material.name[:m.material.name.find(".")]
            m.material.name += "_emission"

            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links

            output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')

            if not Utility.get_nodes_with_type(nodes, "Emission"):
                principled = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
                if principled:
                    if len(principled) == 1:
                        principled = principled[0]
                    else:
                        raise Exception("This material: {} has more than one Diffuse Shader".format(m.name))
                    mix_node = nodes.new(type='ShaderNodeMixShader')

                    Utility.insert_node_instead_existing_link(links, principled.outputs['BSDF'], mix_node.inputs[2], mix_node.outputs['Shader'], output.inputs['Surface'])

                    # The light path node returns 1, if the material is hit by a ray coming from the camera, else it returns 0.
                    # In this way the mix shader will use the principled shader for rendering the color of the ceiling itself, while using the emission shader for lighting the scene.
                    lightPath_node = nodes.new(type='ShaderNodeLightPath')
                    links.new(lightPath_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                    emission_node = nodes.new(type='ShaderNodeEmission')
                    emission_node.inputs['Strength'].default_value = self.config.get_float("ceiling_emission_strength", 1.5)
                    links.new(emission_node.outputs['Emission'], mix_node.inputs[1])
                    self._collection_of_mats["ceiling"][mat_name] = m.material

    def run(self):
        # Make some objects emit lights
        for obj in bpy.context.scene.objects:
            if "modelId" in obj:
                obj_id = obj["modelId"]

                # In the case of the lamp
                if obj_id in self.lights:
                    self._make_lamp_emissive(obj, self.lights[obj_id])

                # Make the windows emit light
                if obj_id in self.windows:
                    self._make_window_emissive(obj)

                # Also make ceilings slightly emit light
                if obj.name.startswith("Ceiling#"):
                    self._make_ceiling_emissive(obj)
