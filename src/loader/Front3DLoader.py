import os
import re
import json
import warnings
from math import radians
import numpy as np

import bpy
import bmesh
import mathutils

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.Config import Config
from src.utility.BlenderUtility import duplicate_objects
from src.utility.LabelIdMapping import LabelIdMapping

class Front3DLoader(LoaderInterface):
    """
    Loads the 3D-Front dataset.

    https://tianchi.aliyun.com/specials/promotion/alibaba-3d-scene-dataset

    Each object gets the name based on the category/type, on top of that you can use a mapping specified in the
    resources/front_3D folder.

    The dataset already supports semantic segmentation with either the 3D-Front classes or the nyu classes.
    As we have created this mapping ourselves it might be faulty.

    The Front3DLoader creates automatically lights in the scene, by adding emission shaders to the ceiling and lamps.
    The strength can be configured via the config.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - json_path
          - Path to the json file, where the house information is stored.
          - string
        * - 3D_future_model_path
          - Path to the models used in the 3D-Front dataset. to the models used in the 3D-Front dataset. Type: str
          - string
        * - mapping_file
          - Path to a file, which maps the names of the objects to ids. Default:
            resources/front_3D/3D_front_mapping.csv
          - string
        * - ceiling_light_strength
          - Strength of the emission shader used in the ceiling. Default: 0.8
          - float
        * - lamp_light_strength
          - Strength of the emission shader used in each lamp. Default: 7.0
          - float
   """

    def __init__(self, config: Config):
        LoaderInterface.__init__(self, config)
        self.json_path = Utility.resolve_path(self.config.get_string("json_path"))
        self.future_model_path = Utility.resolve_path(self.config.get_string("3D_future_model_path"))

        self.mapping_file = Utility.resolve_path(self.config.get_string("mapping_file",
                                                                        os.path.join("resources", "front_3D",
                                                                                     "3D_front_mapping.csv")))
        if not os.path.exists(self.mapping_file):
            raise Exception("The mapping file could not be found: {}".format(self.mapping_file))
        _, self.mapping = LabelIdMapping.read_csv_mapping(self.mapping_file)
        # a list of all newly created objects
        self.created_objects = []



    def run(self):

        if not os.path.exists(self.json_path):
            raise Exception("The given path does not exists: {}".format(self.json_path))
        if not self.json_path.endswith(".json"):
            raise Exception("The given path does not point to a .json file: {}".format(self.json_path))
        if not os.path.exists(self.future_model_path):
            raise Exception("The 3D future model path does not exist: {}".format(self.future_model_path))

        # load data from json file
        with open(self.json_path, "r") as json_file:
            data = json.load(json_file)

        self._create_mesh_objects_from_file(data)

        all_loaded_furniture = self._load_furniture_objs(data)

        self._move_and_duplicate_furniture(data, all_loaded_furniture)

        # add an identifier to the obj
        for obj in self.created_objects:
            obj["is_3d_front"] = True

        self._set_properties(self.created_objects)

    def _create_mesh_objects_from_file(self, data: dir):
        """
        This creates for a given data json block all defined meshes and assigns the correct materials.
        This means that the json file contains some mesh, like walls and floors, which have to built up manually.

        It also already adds the lighting for the ceiling

        :param data: json data dir. Must contain "material" and "mesh"
        """
        # extract all used materials -> there are more materials defined than used
        used_materials = []
        for mat in data["material"]:
            used_materials.append({"uid": mat["uid"], "texture": mat["texture"],
                                   "normaltexture": mat["normaltexture"], "color": mat["color"]})

        col = bpy.data.collections.get("Collection")
        for mesh_data in data["mesh"]:
            # extract the obj name, which also is used as the category_id name
            used_obj_name = mesh_data["type"].strip()
            if used_obj_name == "":
                used_obj_name = "void"
            if "material" not in mesh_data:
                warnings.warn(f"Material is not defined for {used_obj_name} in this file: {self.json_path}")
                continue
            # create a new mesh
            mesh = bpy.data.meshes.new(used_obj_name + "_mesh")  # add the new mesh
            # link this mesh inside of a new object
            obj = bpy.data.objects.new(mesh.name, mesh)
            self.created_objects.append(obj)
            # link the object in the collection
            col.objects.link(obj)
            # set the name of the new object to the category_id name
            obj.name = used_obj_name

            # set two custom properties, first that it is a 3D_future object and second the category_id
            obj["is_3D_future"] = True
            obj["category_id"] = self.mapping[used_obj_name.lower()]

            # get the material uid of the current mesh data
            current_mat = mesh_data["material"]
            used_mat = None
            # search in the used materials after this uid
            for u_mat in used_materials:
                if u_mat["uid"] == current_mat:
                    used_mat = u_mat
                    break
            # If there should be a material used
            if used_mat:
                if used_mat["texture"]:
                    raise Exception("The material should use a texture, this was not implemented yet!")
                if used_mat["normaltexture"]:
                    raise Exception("The material should use a normal texture, this was not implemented yet!")
                # if there is a normal color used
                if used_mat["color"]:
                    # Create a new material
                    mat = bpy.data.materials.new(name=used_obj_name + "_material")
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    # create a principled node and set the default color
                    principled_node = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                    principled_node.inputs["Base Color"].default_value = mathutils.Vector(used_mat["color"]) / 255.0
                    # if the object is a ceiling add some light output
                    if "ceiling" in used_obj_name.lower():
                        links = mat.node_tree.links
                        mix_node = nodes.new(type='ShaderNodeMixShader')
                        output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')
                        Utility.insert_node_instead_existing_link(links, principled_node.outputs['BSDF'],
                                                                  mix_node.inputs[2], mix_node.outputs['Shader'],
                                                                  output.inputs['Surface'])
                        # The light path node returns 1, if the material is hit by a ray coming from the camera,
                        # else it returns 0. In this way the mix shader will use the principled shader for rendering
                        # the color of the lightbulb itself, while using the emission shader for lighting the scene.
                        light_path_node = nodes.new(type='ShaderNodeLightPath')
                        links.new(light_path_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                        emission_node = nodes.new(type='ShaderNodeEmission')
                        # use the same color for the emission light then for the ceiling itself
                        emission_node.inputs["Color"].default_value = mathutils.Vector(used_mat["color"]) / 255.0
                        ceiling_light_strength = self.config.get_float("ceiling_light_strength", 0.8)
                        emission_node.inputs["Strength"].default_value = ceiling_light_strength

                        links.new(emission_node.outputs["Emission"], mix_node.inputs[1])

                    # as this material was just created the material is just appened to the empty list
                    obj.data.materials.append(mat)

            # extract the vertices from the mesh_data
            vert = [float(ele) for ele in mesh_data["xyz"]]
            # extract the faces from the mesh_data
            faces = mesh_data["faces"]
            # extract the normals from the mesh_data
            normal = [float(ele) for ele in mesh_data["normal"]]

            # map those to the blender coordinate system
            num_vertices = int(len(vert) / 3)
            vertices = np.reshape(np.array(vert), [num_vertices, 3])
            normal = np.reshape(np.array(normal), [num_vertices, 3])
            # flip the first and second value
            vertices[:, 1], vertices[:, 2] = vertices[:, 2], vertices[:, 1].copy()
            normal[:, 1], normal[:, 2] = normal[:, 2], normal[:, 1].copy()
            # reshape back to a long list
            vertices = np.reshape(vertices, [num_vertices * 3])
            normal = np.reshape(normal, [num_vertices * 3])

            # add this new data to the mesh object
            mesh = obj.data
            mesh.vertices.add(num_vertices)
            mesh.vertices.foreach_set("co", vertices)
            mesh.vertices.foreach_set("normal", normal)

            # link the faces as vertex indices
            num_vertex_indicies = len(faces)
            mesh.loops.add(num_vertex_indicies)
            mesh.loops.foreach_set("vertex_index", faces)

            # the loops are set based on how the faces are a ranged
            num_loops = int(num_vertex_indicies / 3)
            mesh.polygons.add(num_loops)
            # always 3 vertices form one triangle
            loop_start = np.arange(0, num_vertex_indicies, 3)
            # the total size of each triangle is therefore 3
            loop_total = [3] * num_loops
            mesh.polygons.foreach_set("loop_start", loop_start)
            mesh.polygons.foreach_set("loop_total", loop_total)

            # the uv coordinates are reshaped then the face coords are extracted
            uv = np.reshape(np.array([float(ele) for ele in mesh_data["uv"]]), [num_vertices, 2])
            used_uvs = uv[faces, :]
            # and again reshaped back to the long list
            used_uvs = np.reshape(used_uvs, [2 * num_vertex_indicies])

            mesh.uv_layers.new(name="new_uv_layer")
            mesh.uv_layers[-1].data.foreach_set("uv", used_uvs)

            # this update converts the upper data into a mesh
            mesh.update()

            # the generation might fail if the data does not line up
            # this is not used as even if the data does not line up it is still able to render the objects
            # We assume that not all meshes in the dataset do conform with the mesh standards set in blender
            #result = mesh.validate(verbose=False)
            #if result:
            #    raise Exception("The generation of the mesh: {} failed!".format(used_obj_name))

    def _load_furniture_objs(self, data: dir):
        """
        Load all furniture objects specified in the json file, these objects are stored as "raw_model.obj" in the
        3D_future_model_path. For lamp the lamp_light_strength value can be changed via the config.

        :param data: json data dir. Should contain "furniture"
        :return: all objects which have been loaded
        """
        # collect all loaded furniture objects
        all_objs = []
        # for each furniture element
        for ele in data["furniture"]:
            # create the paths based on the "jid"
            folder_path = os.path.join(self.future_model_path, ele["jid"])
            obj_file = os.path.join(folder_path, "raw_model.obj")
            # if the object exists load it -> a lot of object do not exist
            # we are unsure why this is -> we assume that not all objects have been made public
            if os.path.exists(obj_file):
                # load all objects from this .obj file
                objs = Utility.import_objects(filepath=obj_file)
                # extract the name, which serves as category id
                used_obj_name = ele["category"]
                for obj in objs:
                    obj.name = used_obj_name
                    # add some custom properties
                    obj["uid"] = ele["uid"]
                    # this custom property determines if the object was used before
                    # is needed to only clone the second appearance of this object
                    obj["is_used"] = False
                    obj["is_3D_future"] = True
                    obj["type"] = "Non-Object"  # is an non object used for the interesting score
                    # set the category id based on the used obj name
                    obj["category_id"] = self.mapping[used_obj_name.lower()]
                    # walk over all material slots
                    for slot in obj.material_slots:
                        mat = slot.material
                        nodes = mat.node_tree.nodes
                        links = mat.node_tree.links

                        principled_node = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
                        is_lamp = "lamp" in used_obj_name.lower()
                        if len(principled_node) == 0 and is_lamp:
                            # this material has already been transformed
                            continue
                        elif len(principled_node) == 1:
                            principled_node = principled_node[0]
                        else:
                            raise Exception("The amount of principle nodes can not be more than 1, "
                                            "for obj: {}!".format(obj.name))

                        # For each a texture node
                        image_node = nodes.new(type='ShaderNodeTexImage')
                        # and load the texture.png
                        base_image_path = os.path.join(folder_path, "texture.png")
                        image_node.image = bpy.data.images.load(base_image_path, check_existing=True)
                        links.new(image_node.outputs['Color'], principled_node.inputs['Base Color'])
                        # if the object is a lamp, do the same as for the ceiling and add an emission shader
                        if is_lamp:
                            mix_node = nodes.new(type='ShaderNodeMixShader')
                            output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')
                            Utility.insert_node_instead_existing_link(links, principled_node.outputs['BSDF'],
                                                                      mix_node.inputs[2], mix_node.outputs['Shader'],
                                                                      output.inputs['Surface'])

                            # The light path node returns 1, if the material is hit by a ray coming from the camera,
                            # else it returns 0. In this way the mix shader will use the principled shader for
                            # rendering the color of the lightbulb itself, while using the emission shader
                            # for lighting the scene.
                            lightPath_node = nodes.new(type='ShaderNodeLightPath')
                            links.new(lightPath_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                            emission_node = nodes.new(type='ShaderNodeEmission')
                            lamp_light_strength = self.config.get_float("lamp_light_strength", 7.0)
                            emission_node.inputs["Strength"].default_value = lamp_light_strength
                            links.new(image_node.outputs['Color'], emission_node.inputs['Color'])

                            links.new(emission_node.outputs["Emission"], mix_node.inputs[1])

                all_objs.extend(objs)
        return all_objs

    def _move_and_duplicate_furniture(self, data: dir, all_loaded_furniture: list):
        """
        Move and duplicate the furniture depending on the data in the data json dir.
        After loading each object gets a location based on the data in the json file. Some objects are used more than
        once these are duplicated and then placed.

        :param data: json data dir. Should contain "scene", which should contain "room"
        :param all_loaded_furniture: all objects which have been loaded in _load_furniture_objs
        """
        # this rotation matrix rotates the given quaternion into the blender coordinate system
        blender_rot_mat = mathutils.Matrix.Rotation(radians(-90), 4, 'X')
        if "scene" not in data:
            raise Exception("There is no scene data in this json file: {}".format(self.json_path))
        # for each room
        for room_id, room in enumerate(data["scene"]["room"]):
            # for each object in that room
            for child in room["children"]:
                if "furniture" in child["instanceid"]:
                    # find the object where the uid matches the child ref id
                    for obj in all_loaded_furniture:
                        if obj["uid"] == child["ref"]:
                            # if the object was used before, duplicate the object and move that duplicated obj
                            if obj["is_used"]:
                                new_obj = duplicate_objects(obj)[0]
                            else:
                                # if it is the first time use the object directly
                                new_obj = obj
                            self.created_objects.append(new_obj)
                            new_obj["is_used"] = True
                            new_obj["room_id"] = room_id
                            new_obj["type"] = "Object"  # is an object used for the interesting score
                            new_obj["coarse_grained_class"] = new_obj["category_id"]
                            # this flips the y and z coordinate to bring it to the blender coordinate system
                            new_obj.location = mathutils.Vector(child["pos"]).xzy
                            new_obj.scale = child["scale"]
                            # extract the quaternion and convert it to a rotation matrix
                            rotation_mat = mathutils.Quaternion(child["rot"]).to_euler().to_matrix().to_4x4()
                            # transform it into the blender coordinate system and then to an euler
                            new_obj.rotation_euler = (blender_rot_mat @ rotation_mat).to_euler()
