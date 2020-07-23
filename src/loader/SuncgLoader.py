import csv
import json
import math
import os

import bpy
from mathutils import Matrix

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.LabelIdMapping import LabelIdMapping


class SuncgLoader(LoaderInterface):
    """ Loads a house.json file into blender.

     - Loads all objects files specified in the house.json file.
     - Orders them hierarchically (level -> room -> object)
     - Writes metadata into the custom properties of each object

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

        "path", "The path to the house.json file which should be loaded. Type: string."
        "suncg_path", "The path to the suncg root directory which should be used for loading objects, rooms, textures "
                      "etc. Type: string. Default: is extracted from the house.json path"
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)
        self.house_path = Utility.resolve_path(self.config.get_string("path"))
        suncg_folder_path = os.path.join(os.path.dirname(self.house_path), "../..")
        self.suncg_dir = self.config.get_string("suncg_path", suncg_folder_path)
        self._collection_of_loaded_objs = {}
        # there are only two types of materials, textures and diffuse
        self._collection_of_loaded_mats = {"texture": {}, "diffuse": {}}
        LabelIdMapping.assign_mapping(Utility.resolve_path(os.path.join('resources', 'id_mappings', 
            'nyu_idset.csv')))

    def run(self):
        with open(Utility.resolve_path(self.house_path), "r") as f:
            config = json.load(f)

        self._read_model_category_mapping(os.path.join('resources','suncg','Better_labeling_for_NYU.csv'))

        house_id = config["id"]

        for level in config["levels"]:
            # Build empty level object which acts as a parent for all rooms on the level
            level_obj = bpy.data.objects.new("Level#" + level["id"], None)
            level_obj["type"] = "Level"
            if "bbox" in level:
                level_obj["bbox"] = self._correct_bbox_frame(level["bbox"])
            else:
                print("Warning: The level with id " + level["id"] + " is missing the bounding box attribute in the given house.json file!")
            bpy.context.scene.collection.objects.link(level_obj)

            room_per_object = {}

            for node in level["nodes"]:
                # Skip invalid nodes (This is the same behavior as in the SUNCG Toolbox)
                if "valid" in node and node["valid"] == 0:
                    continue

                # Metadata is directly stored in the objects custom data
                metadata = {
                    "type": node["type"]
                }

                if "modelId" in node:
                    metadata["modelId"] = node["modelId"]

                    if node["modelId"] in self.object_fine_grained_label_map:
                        metadata["fine_grained_class"] = self.object_fine_grained_label_map[node["modelId"]]
                        metadata["coarse_grained_class"] = self.object_coarse_grained_label_map[node["modelId"]]
                        metadata["category_id"] = self._get_label_id(node["modelId"])

                if "bbox" in node:
                    metadata["bbox"] = self._correct_bbox_frame(node["bbox"])

                if "transform" in node:
                    transform = Matrix([node["transform"][i*4:(i+1)*4] for i in range(4)])
                    # Transpose, as given transform matrix was col-wise, but blender expects row-wise
                    transform.transpose()
                else:
                    transform = None

                if "materials" in node:
                    material_adjustments = node["materials"]
                else:
                    material_adjustments = []

                # Lookup if the object belongs to a room
                object_id = int(node["id"].split("_")[-1])
                if object_id in room_per_object:
                    parent = room_per_object[object_id]
                else:
                    parent = level_obj

                if node["type"] == "Room":
                    self._load_room(node, metadata, material_adjustments, transform, house_id, level_obj, room_per_object)
                elif node["type"] == "Ground":
                    self._load_ground(node, metadata, material_adjustments, transform, house_id, parent)
                elif node["type"] == "Object":
                    self._load_object(node, metadata, material_adjustments, transform, parent)
                elif node["type"] == "Box":
                    self._load_box(node, material_adjustments, transform, parent)
        self._rename_materials()

    def _rename_materials(self):
        """
        Rename all materials based on their texture if they have one

        This makes the accessing later on easier
        """

        for material in bpy.data.materials:
            if material.use_nodes:
                nodes = material.node_tree.nodes
                textures = Utility.get_nodes_with_type(nodes, "ShaderNodeTexImage")
                if len(textures) == 1:
                    material.name = textures[0].image.name


    def _load_room(self, node, metadata, material_adjustments, transform, house_id, parent, room_per_object):
        """ Load the room specified in the given node.

        :param node: The node dict which contains information from house.json..
        :param metadata: A dict of metadata which will be written into the object's custom data.
        :param material_adjustments: Adjustments to the materials which were specified inside house.json.
        :param transform: The transformation that should be applied to the loaded objects.
        :param house_id: The id of the current house.
        :param parent: The parent object to which the room should be linked
        :param room_per_object: A dict for object -> room lookup (Will be written into)
        """
        # Build empty room object which acts as a parent for all objects inside
        room_obj = bpy.data.objects.new("Room#" + node["id"], None)
        room_obj["type"] = "Room"
        room_obj["bbox"] = self._correct_bbox_frame(node["bbox"])
        room_obj["roomTypes"] = node["roomTypes"]
        room_obj.parent = parent
        bpy.context.scene.collection.objects.link(room_obj)
        # Store indices of all contained objects in
        if "nodeIndices" in node:
            for child_id in node["nodeIndices"]:
                room_per_object[child_id] = room_obj

        if "hideFloor" not in node or node["hideFloor"] != 1:
            metadata["type"] = "Floor"
            metadata["category_id"] = LabelIdMapping.label_id_map["floor"]
            metadata["fine_grained_class"] = "floor"
            self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "f.obj"), metadata, material_adjustments, transform, room_obj)

        if "hideCeiling" not in node or node["hideCeiling"] != 1:
            metadata["type"] = "Ceiling"
            metadata["category_id"] = LabelIdMapping.label_id_map["ceiling"]
            metadata["fine_grained_class"] = "ceiling"
            self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "c.obj"), metadata, material_adjustments, transform, room_obj)

        if "hideWalls" not in node or node["hideWalls"] != 1:
            metadata["type"] = "Wall"
            metadata["category_id"] = LabelIdMapping.label_id_map["wall"]
            metadata["fine_grained_class"] = "wall"
            self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "w.obj"), metadata, material_adjustments, transform, room_obj)

    def _load_ground(self, node, metadata, material_adjustments, transform, house_id, parent):
        """ Load the ground specified in the given node.

        :param node: The node dict which contains information from house.json..
        :param metadata: A dict of metadata which will be written into the object's custom data.
        :param material_adjustments: Adjustments to the materials which were specified inside house.json.
        :param transform: The transformation that should be applied to the loaded objects.
        :param house_id: The id of the current house.
        :param parent: The parent object to which the ground should be linked
        """
        metadata["type"] = "Ground"
        metadata["category_id"] = LabelIdMapping.label_id_map["floor"]
        metadata["fine_grained_class"] = "ground"
        self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "f.obj"), metadata, material_adjustments, transform, parent)

    def _load_object(self, node, metadata, material_adjustments, transform, parent):
        """ Load the object specified in the given node.

        :param node: The node dict which contains information from house.json..
        :param metadata: A dict of metadata which will be written into the object's custom data.
        :param material_adjustments: Adjustments to the materials which were specified inside house.json.
        :param transform: The transformation that should be applied to the loaded objects.
        :param parent: The parent object to which the ground should be linked
        """
        if "state" not in node or node["state"] == 0:
            self._load_obj(os.path.join(self.suncg_dir, "object", node["modelId"], node["modelId"] + ".obj"), metadata, material_adjustments, transform, parent)
        else:
            self._load_obj(os.path.join(self.suncg_dir, "object", node["modelId"], node["modelId"] + "_0.obj"), metadata, material_adjustments, transform, parent)

    def _correct_bbox_frame(self, bbox):
        """ Corrects the coordinate frame of the given bbox.

        :param bbox: The bbox.
        :return: The corrected bbox.
        """
        return {
            "min": Utility.transform_point_to_blender_coord_frame(bbox["min"], ["X", "-Z", "Y"]),
            "max": Utility.transform_point_to_blender_coord_frame(bbox["max"], ["X", "-Z", "Y"])
        }

    def _load_box(self, node, material_adjustments, transform, parent):
        """ Creates a cube inside blender which follows the specifications of the given node.

        :param node: The node dict which contains information from house.json..
        :param material_adjustments: Adjustments to the materials which were specified inside house.json.
        :param transform: The transformation that should be applied to the loaded objects.
        :param parent: The parent object to which the ground should be linked
        """
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        box = bpy.context.object
        box.name = "Box#" + node["id"]
        box.matrix_world = Matrix.Identity(4)
        # Scale the cube to the required dimensions
        box.matrix_world @= Matrix.Scale(node["dimensions"][0] / 2, 4, (1.0, 0.0, 0.0)) @ Matrix.Scale(node["dimensions"][1] / 2, 4, (0.0, 1.0, 0.0)) @ Matrix.Scale(node["dimensions"][2] / 2, 4, (0.0, 0.0, 1.0))

        # Create UV mapping (beforehand we apply the scaling from the previous step, such that the resulting uv mapping has the correct aspect)
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.editmode_toggle()
        bpy.ops.uv.cube_project()
        bpy.ops.object.editmode_toggle()

        # Create an empty material which is filled in the next step
        mat = bpy.data.materials.new(name="material_0")
        mat.use_nodes = True
        box.data.materials.append(mat)

        self._transform_and_colorize_object(box, material_adjustments, transform, parent)
        # set class to void
        box["category_id"] = LabelIdMapping.label_id_map["void"]
        # Rotate cube to match objects loaded from .obj, has to be done after transformations have been applied
        box.matrix_world = Matrix.Rotation(math.radians(90), 4, "X") @ box.matrix_world

        # Set the physics property of all imported boxes
        self._set_properties(bpy.context.selected_objects)

    def _load_obj(self, path, metadata, material_adjustments, transform=None, parent=None):
        """ Load the wavefront object file from the given path and adjust according to the given arguments.

        :param path: The path to the .obj file.
        :param metadata: A dict of metadata which will be written into the object's custom data.
        :param material_adjustments: Adjustments to the materials which were specified inside house.json.
        :param transform: The transformation that should be applied to the loaded objects.
        :param parent: The parent object to which the object should be linked
        """
        if not os.path.exists(path):
            print("Warning: " + path + " is missing")
        else:
            object_already_loaded = path in self._collection_of_loaded_objs
            loaded_objects = Utility.import_objects(filepath=path, cached_objects=self._collection_of_loaded_objs)
            if object_already_loaded:
                print("Duplicate object: {}".format(path))
                for object in loaded_objects:
                    # the original object matrix from the .obj loader -> is not an identity matrix
                    object.matrix_world = Matrix([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
                    # remove all custom properties
                    keys = object.keys()
                    for key in keys:
                        del object[key]
            # Go through all imported objects
            for object in loaded_objects:
                for key in metadata.keys():
                    object[key] = metadata[key]

                self._transform_and_colorize_object(object, material_adjustments, transform, parent)

            # Set the physics property of all imported objects
            self._set_properties(bpy.context.selected_objects)

    def _transform_and_colorize_object(self, object, material_adjustments, transform=None, parent=None):
        """ Applies the given transformation to the object and refactors its materials.

        Material is replaced with an existing material if possible or is changed according to the material_adjustments

        :param object: The object to use.
        :param material_adjustments: A list of adjustments to make. (Each element i corresponds to material_i)
        :param transform: The transformation matrix to apply
        :param parent: The parent object to which the object should be linked
        """
        if parent is not None:
            object.parent = parent

        if transform is not None:
            # Apply transformation
            object.matrix_world @= transform


        for mat_slot in object.material_slots:
            mat = mat_slot.material

            # the material name of an object contains a nr, which is mentioned in the material_adjustments
            index = mat.name[mat.name.find("_") + 1:]
            if "." in index:
                index = index[:index.find(".")]
            index = int(index)

            # check if this index is mentioned in material_adjustments and if a texture is necessary
            force_texture = index < len(material_adjustments) and "texture" in material_adjustments[index]
            self._recreate_material_nodes(mat, force_texture)

            if index < len(material_adjustments):
                self._adjust_material_nodes(mat, material_adjustments[index])
            mat_type, value = self._get_type_and_value_from_mat(mat)
            current_mats = self._collection_of_loaded_mats[mat_type]
            if value in current_mats:
                mat_slot.material = current_mats[value]
            else:
                # save the current material for later
                current_mats[value] = mat


    def _get_type_and_value_from_mat(self, mat):
        """
        Returns the type of the material -> either diffuse or with texture (there are only two in SUNCG)
        :param mat: the material where the type and value should be determined
        :return mat_type, value: mat_type is either "diffuse" or "texture", the value contains either name of the
                                 image or the color mapped to an RGB string of the values
        """
        nodes = mat.node_tree.nodes
        image_node = Utility.get_nodes_with_type(nodes, 'TexImage')
        if len(image_node) == 1:
            # there is an image node -> type texture
            mat_type = "texture"
            image_node = image_node[0]
            if image_node.image is None:
                raise Exception("The image does not have a texture for material: {}".format(mat.name))
            value = image_node.image.name
            if "." in value:
                value = value[:value.find(".")]
        else:
            mat_type = "diffuse"
            principled_node = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
            used_keys = list(principled_node.inputs["Base Color"].default_value)
            alpha = principled_node.inputs['Alpha'].default_value
            used_keys.append(alpha)
            value = "_".join([str(int(255.*ele)) for ele in used_keys])
        return mat_type, value

    def _recreate_material_nodes(self, mat, force_texture):
        """ Remove all nodes and recreate a diffuse node, optionally with texture.

        This will replace all material nodes with only a diffuse and a texturing node (to speedup rendering).

        :param mat: The blender material
        :param force_texture: True, if there always should be a texture node created even if the material has at the moment no texture
        """
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        image_node = Utility.get_nodes_with_type(nodes, 'TexImage')
        # if there is no image no create one
        if force_texture and len(image_node) == 0:
            # The principled BSDF node contains all imported material properties
            principled_node = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")

            uv_node = nodes.new(type='ShaderNodeTexCoord')
            # create an image node and link it
            image_node = nodes.new(type='ShaderNodeTexImage')
            links.new(uv_node.outputs['UV'], image_node.inputs['Vector'])
            links.new(image_node.outputs['Color'], principled_node.inputs['Base Color'])


    def _adjust_material_nodes(self, mat, adjustments):
        """ Adjust the material node of the given material according to the given adjustments.

        Textures or diffuse colors will be changed according to the given material_adjustments.

        :param mat: The blender material.
        :param adjustments: A dict containing a new "diffuse" color or a new "texture" path
        """
        nodes = mat.node_tree.nodes

        if "diffuse" in adjustments:
            principle_node = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
            principle_node.inputs['Base Color'].default_value = Utility.hex_to_rgba(adjustments["diffuse"])

        if "texture" in adjustments:
            image_path = os.path.join(self.suncg_dir, "texture", adjustments["texture"])
            image_path = Utility.resolve_path(image_path)

            if os.path.exists(image_path + ".png"):
                image_path += ".png"
            else:
                image_path += ".jpg"

            image_node = Utility.get_the_one_node_with_type(nodes, "ShaderNodeTexImage")
            if os.path.exists(image_path):
                image_node.image = bpy.data.images.load(image_path, check_existing=True)
            else:
                print("Warning: Cannot load texture, path does not exist: {}, remove image node again".format(image_path))
                nodes.remove(image_node)

    def _read_model_category_mapping(self, path):
        """ Reads in the model category mapping csv.

        :param path: The path to the csv file.
        """
        self.windows = []       
        self.object_label_map = {}      
        self.object_fine_grained_label_map = {}
        self.object_coarse_grained_label_map = {}              
        
        with open(Utility.resolve_path(path), 'r') as csvfile:      
            reader = csv.DictReader(csvfile)        
            for row in reader:      
                self.object_label_map[row["model_id"]] = row["nyuv2_40class"]       
                self.object_fine_grained_label_map[row["model_id"]] = row["fine_grained_class"]     
                self.object_coarse_grained_label_map[row["model_id"]] = row["coarse_grained_class"]     
        
        # Use the void category as label for the world background
        bpy.context.scene.world["category_id"] = LabelIdMapping.label_id_map["void"]

    def _get_label_id(self, obj_id):
        """ Returns the label id for an object with the given model_id.

        :param obj_id: The model_id of the object.
        :return: The corresponding label index.
        """
        return LabelIdMapping.label_id_map[self.object_label_map[obj_id]]
