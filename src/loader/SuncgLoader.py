from src.main.Module import Module
import bpy
import json
import os
from mathutils import Matrix, Vector, Euler
import math

from src.utility.Utility import Utility


class SuncgLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)
        self.house_path = self.config.get_string("path")
        self.suncg_dir = self.config.get_string("suncg_path", os.path.join(os.path.dirname(self.house_path), "../.."))

    def run(self):
        with open(Utility.resolve_path(self.house_path), "r") as f:
            config = json.load(f)

        house_id = config["id"]

        for level in config["levels"]:
            for node in level["nodes"]:
                metadata = {
                    "type": node["type"],
                    "modelId": node["modelId"]
                }

                if "transform" in node:
                    transform = Matrix([node["transform"][i*4:(i+1)*4] for i in range(4)])
                    transform.transpose()
                else:
                    transform = None

                if "materials" in node:
                    material_adjustments = node["materials"]
                else:
                    material_adjustments = []

                if node["type"] == "Room":
                    # Floor
                    self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "f.obj"), metadata, material_adjustments, transform)
                    # Ceiling
                    self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "c.obj"), metadata, material_adjustments, transform)
                    # Walls
                    self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "w.obj"), metadata, material_adjustments, transform)
                elif node["type"] == "Ground":
                    self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "f.obj"), metadata, material_adjustments, transform)
                elif node["type"] == "Object":
                    if node["state"] == 0:
                        self._load_obj(os.path.join(self.suncg_dir, "object", node["modelId"], node["modelId"] + ".obj"), metadata, material_adjustments, transform)
                    else:
                        self._load_obj(os.path.join(self.suncg_dir, "object", node["modelId"], node["modelId"] + "_0.obj"), metadata, material_adjustments, transform)

    def _load_obj(self, path, metadata, material_adjustments, transform=None):
        if not os.path.exists(path):
            print("Warning: " + path + " is missing")
        else:
            bpy.ops.import_scene.obj(filepath=path)

            for object in bpy.context.selected_objects:
                for key in metadata.keys():
                    object[key] = metadata[key]

                if transform is not None:
                    object.matrix_world = Matrix.Rotation(math.radians(90), 4, "X") * transform

                for mat_slot in object.material_slots:
                    mat = mat_slot.material

                    index = mat.name[mat.name.find("_") + 1:]
                    if "." in index:
                        index = index[:index.find(".")]
                    index = int(index)

                    if index < len(material_adjustments):
                        adjustments = material_adjustments[index]

                        nodes = mat.node_tree.nodes
                        for node in nodes:
                            nodes.remove(node)
                        links = mat.node_tree.links

                        has_texture = (len(mat.texture_slots) > 0 and mat.texture_slots[0] is not None) or "texture" in adjustments

                        output_node = nodes.new(type='ShaderNodeOutputMaterial')
                        diffuse_node = nodes.new(type='ShaderNodeBsdfDiffuse')
                        if has_texture:
                            uv_node = nodes.new(type='ShaderNodeTexCoord')
                            image_node = nodes.new(type='ShaderNodeTexImage')

                        links.new(diffuse_node.outputs[0], output_node.inputs[0])
                        if has_texture:
                            links.new(image_node.outputs[0], diffuse_node.inputs[0])
                            links.new(uv_node.outputs[2], image_node.inputs[0])

                        diffuse_node.inputs[0].default_value[:3] = mat.diffuse_color
                        if len(mat.texture_slots) > 0 and mat.texture_slots[0] is not None:
                            image_node.image = mat.texture_slots[0].texture.image

                        if "diffuse" in adjustments:
                            diffuse_node.inputs[0].default_value = Utility.hex_to_rgba(adjustments["diffuse"])

                        if "texture" in adjustments:
                            image_path = os.path.join(self.suncg_dir, "texture", adjustments["texture"])
                            if os.path.exists(image_path + ".png"):
                                image_path += ".png"
                            else:
                                image_path += ".jpg"

                            image_node.image = bpy.data.images.load(image_path, check_existing=True)