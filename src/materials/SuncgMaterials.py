from src.main.Module import Module
import bpy
import csv

from src.utility.Utility import Utility


class SuncgMaterials(Module):

    def __init__(self, config):
        Module.__init__(self, config)

        # Read in lights
        self.lights = {}
        # File format: <obj id> <number of lightbulb materials> <lightbulb material names> <number of lampshade materials> <lampshade material names>
        with open(Utility.resolve_path("suncg/light_geometry_compact.txt")) as f:
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
        with open(Utility.resolve_path('suncg/ModelCategoryMapping.csv'), 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["coarse_grained_class"] == "window":
                    self.windows.append(row["model_id"])

    def _get_model_id(self, obj):
        if "modelId" in obj:
            return obj["modelId"]

    def _make_lamp_emissive(self, obj, light):
        for m in obj.material_slots:
            mat_name = m.material.name
            if "." in mat_name:
                mat_name = mat_name[:mat_name.find(".")]

            if mat_name in light[0] or mat_name in light[1]:
                nodes = m.material.node_tree.nodes
                links = m.material.node_tree.links

                output = nodes.get("Material Output")
                emission = nodes.get("Emission")
                if emission is None:
                    diffuse = nodes.get("Diffuse BSDF")
                    if diffuse is not None:
                        mix_node = nodes.new(type='ShaderNodeMixShader')
                        Utility.insert_node_instead_existing_link(links, diffuse.outputs[0], mix_node.inputs[2], mix_node.outputs[0], output.inputs[0])

                        lightPath_node = nodes.new(type='ShaderNodeLightPath')
                        links.new(lightPath_node.outputs[0], mix_node.inputs[0])

                        emission_node = nodes.new(type='ShaderNodeEmission')
                        emission_node.inputs[0].default_value = m.material.diffuse_color

                        if mat_name in light[0]:
                            # If the material corresponds to light bulb
                            emission_node.inputs[1].default_value = self.config.get_float("lightbulb_emission_strength", 15)
                        else:
                            # If the material corresponds to a lampshade
                            emission_node.inputs[1].default_value = self.config.get_float("lampshade_emission_strength", 7)

                        links.new(emission_node.outputs[0], mix_node.inputs[1])

    def _make_window_emissive(self, obj):
        for m in obj.material_slots:
            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links

            principled_node = nodes.get("Principled BSDF")
            alpha = principled_node.inputs[18].default_value

            if alpha < 1:
                emission = nodes.get("Emission")
                if emission is None:
                    output = nodes.get("Material Output")
                    if output is not None:
                        link = next(l for l in links if l.to_socket == output.inputs[0])
                        links.remove(link)

                        mix_node = nodes.new(type='ShaderNodeMixShader')
                        emission_node = nodes.new(type='ShaderNodeEmission')
                        transparent_node = nodes.new(type='ShaderNodeBsdfDiffuse')
                        transparent_node.inputs[0].default_value[:3] = (0.285, 0.5, 0.48)
                        lightPath_node = nodes.new(type='ShaderNodeLightPath')

                        links.new(mix_node.outputs[0], output.inputs[0])
                        links.new(lightPath_node.outputs[0], mix_node.inputs[0])
                        links.new(emission_node.outputs[0], mix_node.inputs[1])
                        links.new(transparent_node.outputs[0], mix_node.inputs[2])

                        emission_node.inputs[0].default_value = (1, 1, 1, 1)
                        emission_node.inputs[1].default_value = 10

    def _make_ceiling_emissive(self, obj):
        for m in obj.material_slots:
            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links

            output = nodes.get("Material Output")
            emission = nodes.get("Emission")
            if emission is None:
                diffuse = nodes.get("Diffuse BSDF")
                if diffuse is not None:
                    mix_node = nodes.new(type='ShaderNodeMixShader')

                    Utility.insert_node_instead_existing_link(links, diffuse.outputs[0], mix_node.inputs[2], mix_node.outputs[0], output.inputs[0])

                    lightPath_node = nodes.new(type='ShaderNodeLightPath')
                    links.new(lightPath_node.outputs[0], mix_node.inputs[0])

                    emission_node = nodes.new(type='ShaderNodeEmission')
                    emission_node.inputs[1].default_value = self.config.get_float("ceiling_emission_strength", 1.5)
                    links.new(emission_node.outputs[0], mix_node.inputs[1])

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
