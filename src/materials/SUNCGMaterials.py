from src.main.Module import Module
import bpy
import csv

from src.utility.Utility import Utility


class SUNCGMaterials(Module):

    def __init__(self, config):
        Module.__init__(self, config)

        # Read in lights
        self.lights = {}
        with open(Utility.resolve_path("suncg/light_geometry_compact.txt")) as f:
            lines = f.readlines()
            for row in lines:
                row = row.strip().split()
                self.lights[row[0]] = [[], []]

                index = 1

                number = int(row[index])
                index += 1

                for i in range(number):
                    self.lights[row[0]][0].append(row[index])
                    index += 1

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

    def run(self):
        # Make some objects emit lights
        for obj in bpy.context.scene.objects:
            if obj.name.startswith("Model#") or ("#" not in obj.name and obj.name.replace(".", "").isdigit()):
                if "#" in obj.name:
                    obj_id = obj.name[len("Model#"):]
                else:
                    obj_id = obj.name
                if "." in obj.name:
                    obj_id = obj_id[:obj_id.find(".")]

                # In the case of the lamp
                if obj_id in self.lights:
                    for m in obj.material_slots:
                        mat_name = m.material.name[m.material.name.find("_") + 1:]
                        if "." in mat_name:
                            mat_name = mat_name[:mat_name.find(".")]

                        if mat_name in self.lights[obj_id][0] or mat_name in self.lights[obj_id][1]:
                            nodes = m.material.node_tree.nodes
                            links = m.material.node_tree.links

                            output = nodes.get("Material Output")
                            emission = nodes.get("Emission")
                            if emission is None:
                                diffuse = nodes.get("Diffuse BSDF")
                                if diffuse is not None:
                                    mix_node = nodes.new(type='ShaderNodeMixShader')
                                    lightPath_node = nodes.new(type='ShaderNodeLightPath')

                                    link = next(l for l in links if l.from_socket == diffuse.outputs[0])
                                    to_socket = link.to_socket
                                    links.remove(link)

                                    links.new(lightPath_node.outputs[0], mix_node.inputs[0])
                                    links.new(diffuse.outputs[0], mix_node.inputs[2])
                                    links.remove(next(l for l in links if l.to_socket == output.inputs[0]))
                                    links.new(mix_node.outputs[0], output.inputs[0])

                                    emission_node = nodes.new(type='ShaderNodeEmission')
                                    emission_node.inputs[0].default_value = m.material.diffuse_color[:] + (1,)

                                    if mat_name in self.lights[obj_id][0]:
                                        # If the material corresponds to light bulb
                                        emission_node.inputs[1].default_value = 15
                                    else:
                                        # If the material corresponds to a lampshade
                                        emission_node.inputs[1].default_value = 7

                                    links.new(emission_node.outputs[0], mix_node.inputs[1])

                # Make the windows emit light
                if obj_id in self.windows:
                    for m in obj.material_slots:
                        nodes = m.material.node_tree.nodes
                        links = m.material.node_tree.links

                        if m.material.translucency > 0:
                            emission = nodes.get("Emission")
                            if emission is None:
                                output = nodes.get("Material Output")
                                if output is not None:
                                    print("Creating emission for " + obj_id)

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

            # Also make ceilings slightly emit light
            elif obj.name.startswith("Ceiling#"):
                for m in obj.material_slots:
                    nodes = m.material.node_tree.nodes
                    links = m.material.node_tree.links

                    output = nodes.get("Material Output")
                    emission = nodes.get("Emission")
                    if emission is None:
                        diffuse = nodes.get("Diffuse BSDF")
                        if diffuse is not None:
                            mix_node = nodes.new(type='ShaderNodeMixShader')
                            lightPath_node = nodes.new(type='ShaderNodeLightPath')
                            emission_node = nodes.new(type='ShaderNodeEmission')

                            link = next(l for l in links if l.from_socket == diffuse.outputs[0])
                            to_socket = link.to_socket
                            links.remove(link)

                            links.remove(next(l for l in links if l.to_socket == output.inputs[0]))
                            links.new(mix_node.outputs[0], output.inputs[0])

                            links.new(lightPath_node.outputs[0], mix_node.inputs[0])
                            links.new(emission_node.outputs[0], mix_node.inputs[1])
                            links.new(diffuse.outputs[0], mix_node.inputs[2])

                            emission_node.inputs[1].default_value = 1.5

        # Remove all material nodes except diffuse and emission shader
        # This reduces the rendering time but could be removed to increase the rendering quality
        for mat in bpy.data.materials:
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            output = nodes.get("Material Output")
            if nodes.get("Emission") is None:
                diff = nodes.get("Diffuse Shader")
                if diff is None:
                    diff = nodes.get("Diffuse BSDF")
                if diff is None:
                    diff = nodes.get("Diff BSDF")

                if diff is not None:
                    link = next(l for l in links if l.to_socket == output.inputs[0])
                    links.remove(link)
                    links.new(diff.outputs[0], output.inputs[0])
