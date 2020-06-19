import os
import re
import json
from math import radians
import numpy as np

import bpy
import bmesh
import mathutils

from src.loader.Loader import Loader
from src.utility.Utility import Utility
from src.utility.BlenderUtility import duplicate_objects


class Front3DLoader(Loader):

    def __init__(self, config):
        Loader.__init__(self, config)
        self.path = Utility.resolve_path(self.config.get_string("path"))

    def run(self):

        if not os.path.exists(self.path):
            raise Exception("The given path does not exists: {}".format(self.path))
        if not self.path.endswith(".json"):
            raise Exception("The given path does not point to a .json file: {}".format(self.path))

        with open(self.path, "r") as json_file:
            data = json.load(json_file)
        print(data.keys())



        #for key in data.keys():
        #    print(key)
        #    input()
        #    print(data[key])
        used_materials = []
        for mat in data["material"]:
            #print(mat.keys())
            used_materials.append({"uid": mat["uid"], "texture":mat["texture"], "normaltexture": mat["normaltexture"], "color": mat["color"]})
            #print(mat)

        for mesh_data in data["mesh"]:
            current_mat = mesh_data["material"]
            used_mat = None
            for u_mat in used_materials:
                if u_mat["uid"] == current_mat:
                    used_mat = u_mat
                    break
            mesh = bpy.data.meshes.new("myBeautifulMesh")  # add the new mesh
            obj = bpy.data.objects.new(mesh.name, mesh)
            col = bpy.data.collections.get("Collection")
            col.objects.link(obj)

            obj.name = mesh_data["type"]

            if used_mat:
                if used_mat["texture"]:
                    raise Exception("use a texture")
                if used_mat["normaltexture"]:
                    raise Exception("use a normal texture")
                if used_mat["color"]:
                    mat = bpy.data.materials.new(name="NewMat")
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    principled_node = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                    principled_node.inputs["Base Color"].default_value = mathutils.Vector(used_mat["color"]) / 255.0
                    if "Ceiling" in mesh_data["type"]:
                        links = mat.node_tree.links
                        mix_node = nodes.new(type='ShaderNodeMixShader')
                        output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')
                        Utility.insert_node_instead_existing_link(links, principled_node.outputs['BSDF'],
                                                                  mix_node.inputs[2], mix_node.outputs['Shader'],
                                                                  output.inputs['Surface'])

                        # The light path node returns 1, if the material is hit by a ray coming from the camera, else it returns 0.
                        # In this way the mix shader will use the principled shader for rendering the color of the lightbulb itself, while using the emission shader for lighting the scene.
                        lightPath_node = nodes.new(type='ShaderNodeLightPath')
                        links.new(lightPath_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                        emission_node = nodes.new(type='ShaderNodeEmission')
                        emission_node.inputs["Color"].default_value = mathutils.Vector(used_mat["color"]) / 255.0
                        emission_node.inputs["Strength"].default_value = 0.5

                        links.new(emission_node.outputs["Emission"], mix_node.inputs[1])

                    # Assign it to object
                    if obj.data.materials:
                        # assign to 1st material slot
                        obj.data.materials[0] = mat
                    else:
                        # no slots
                        obj.data.materials.append(mat)





            vert = [float(ele) for ele in mesh_data["xyz"]]
            faces = mesh_data["faces"]
            normal = [float(ele) for ele in mesh_data["normal"]]

            num_vertices = int(len(vert) / 3)
            vertices = np.reshape(np.array(vert), [num_vertices, 3])
            normal = np.reshape(np.array(normal), [num_vertices, 3])
            vertices[:, 1], vertices[:, 2] = vertices[:, 2], vertices[:, 1].copy()
            normal[:, 1], normal[:, 2] = normal[:, 2], normal[:, 1].copy()
            vertices = np.reshape(vertices, [num_vertices * 3])
            normal = np.reshape(normal, [num_vertices * 3])

            mesh = obj.data
            mesh.vertices.add(num_vertices)
            mesh.vertices.foreach_set("co", vertices)
            mesh.vertices.foreach_set("normal", normal)

            num_vertex_indicies = len(faces)
            mesh.loops.add(num_vertex_indicies)
            mesh.loops.foreach_set("vertex_index", faces)

            num_loops = int(num_vertex_indicies / 3)
            mesh.polygons.add(num_loops)
            loop_start = np.arange(0, num_vertex_indicies, 3)
            loop_end = [3] * num_loops
            mesh.polygons.foreach_set("loop_start", loop_start)
            mesh.polygons.foreach_set("loop_total", loop_end)


            uv = np.reshape(np.array([float(ele) for ele in mesh_data["uv"]]), [num_vertices, 2])
            used_uvs = uv[faces, :]
            used_uvs = np.reshape(used_uvs, [2 * num_vertex_indicies])

            mesh.uv_layers.new(name="new_uv_layer")
            mesh.uv_layers[-1].data.foreach_set("uv", used_uvs)

            mesh.update()
            result = mesh.validate(verbose=True)
            if result:
                raise Exception("The generation of a mesh failed!")


        goal_dir = "/home/max/Downloads/3D-Front/3D-FUTURE-model"
        used_ids = []
        all_objs = []
        for ele in data["furniture"]:
            path = os.path.join(goal_dir, ele["jid"])
            obj_file = os.path.join(path, "raw_model.obj")
            if os.path.exists(obj_file):
                used_ids.append(ele["jid"])
                print(ele["category"])
                objs = Utility.import_objects(filepath=obj_file)

                category = ele["category"]
                for obj in objs:
                    obj.name = category
                    obj["uid"] = ele["uid"]
                    obj["is_used"] = False
                    for slot in obj.material_slots:
                        mat = slot.material
                        nodes = mat.node_tree.nodes
                        links = mat.node_tree.links

                        print(obj.name)
                        principled_node = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
                        is_lamp = "lamp" in category.lower()
                        if len(principled_node) == 0 and is_lamp:
                            # this material has already been transformed
                            continue
                        elif len(principled_node) == 1:
                            principled_node = principled_node[0]
                        else:
                            raise Exception("The amount of principle nodes can not be more than 1, "
                                            "for obj: {}!".format(obj.name))


                        image_node = nodes.new(type='ShaderNodeTexImage')
                        base_image_path = os.path.join(path, "texture.png")
                        image_node.image = bpy.data.images.load(base_image_path, check_existing=True)
                        links.new(image_node.outputs['Color'], principled_node.inputs['Base Color'])
                        if is_lamp:
                            mix_node = nodes.new(type='ShaderNodeMixShader')
                            output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')
                            Utility.insert_node_instead_existing_link(links, principled_node.outputs['BSDF'],
                                                                      mix_node.inputs[2], mix_node.outputs['Shader'],
                                                                      output.inputs['Surface'])

                            # The light path node returns 1, if the material is hit by a ray coming from the camera, else it returns 0.
                            # In this way the mix shader will use the principled shader for rendering the color of the lightbulb itself, while using the emission shader for lighting the scene.
                            lightPath_node = nodes.new(type='ShaderNodeLightPath')
                            links.new(lightPath_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                            emission_node = nodes.new(type='ShaderNodeEmission')
                            emission_node.inputs["Strength"].default_value = 15.0
                            links.new(image_node.outputs['Color'], emission_node.inputs['Color'])

                            links.new(emission_node.outputs["Emission"], mix_node.inputs[1])


                all_objs.extend(objs)
        def conv(vec):
            return [vec[0], vec[2], vec[1]]
        def convq(vec):
            return [vec[0], vec[1], vec[2], vec[3]]
        c = 0
        rot_mat = mathutils.Matrix.Rotation(radians(-90), 4, 'X')
        for room in data["scene"]["room"]:
            for child in room["children"]:
                if "furniture" in child["instanceid"]:
                    for obj in all_objs:
                        if obj["uid"] == child["ref"]:
                            if obj["is_used"]:
                                new_obj = duplicate_objects(obj)[0]
                            else:
                                new_obj = obj
                            new_obj["is_used"] = True
                            new_obj.location = conv(child["pos"])
                            new_obj.scale = child["scale"]
                            new_obj.rotation_euler = (rot_mat @ mathutils.Quaternion(convq(child["rot"])).to_euler().to_matrix().to_4x4()).to_euler()
                            c += 1
        print(len(used_ids))
        print(c)
        print(len(data["scene"]["room"][0]["children"]))


