
import os
import glob
import random

import csv

import bpy


from src.loader.Loader import Loader
from src.utility.Utility import Utility


class SceneNetLoader(Loader):

    def __init__(self, config):
        Loader.__init__(self, config)

        self._file_path = Utility.resolve_path(self.config.get_string("file_path"))

        self._texture_folder = Utility.resolve_path(self.config.get_string("texture_folder"))
        default_category_labeling_path = "resources/scenenet/CategoryLabeling.csv"
        self._category_labeling_path = Utility.resolve_path(self.config.get_string("category_labeling",
                                                                              default_category_labeling_path))
        self._category_labels = {}
        if os.path.exists(self._category_labeling_path):
            with open(self._category_labeling_path, "r") as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=',')
                for line in csv_reader:
                    if "LabelNumber" in line.keys() and "LabelName" in line.keys():
                        self._category_labels[line["LabelName"].lower()] = int(line["LabelNumber"])
            if not self._category_labels:
                raise Exception("The csv file must have been empty: {}".format(self._category_labeling_path))
            bpy.data.scenes["Scene"]["num_labels"] = len(self._category_labels)
            bpy.context.scene.world["category_id"] = self._category_labels["void"]
        else:
            print("Warning: The category labeling file could not be found -> no semantic segmentation available!")


    def run(self):
        # load the objects
        loaded_objects = Utility.import_objects(filepath=self._file_path)
        # sample materials for each object
        self._random_sample_materials_for_each_obj(loaded_objects)

        # set the category ids for each object
        self._set_category_ids(loaded_objects)

        # add custom properties
        self._set_properties(loaded_objects)

    def _random_sample_materials_for_each_obj(self, loaded_objects):
        # for each object add a material
        for obj in loaded_objects:
            for mat_slot in obj.material_slots:
                material = mat_slot.material
                nodes = material.node_tree.nodes
                links = material.node_tree.links
                principled_bsdf = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
                if principled_bsdf and len(principled_bsdf) == 1:
                    principled_bsdf = principled_bsdf[0]
                else:
                    raise Exception("Warning: The generation of the material failed, it has more than one Prinicipled BSDF!")
                output_node = Utility.get_nodes_with_type(nodes, "OutputMaterial")
                if output_node and len(output_node) == 1:
                    output_node = output_node[0]
                else:
                    raise Exception("Warning: The generation of the material failed, it has more than one Output Material!")
                texture_nodes = Utility.get_nodes_with_type(nodes, "ShaderNodeTexImage")
                if not texture_nodes:
                    texture_node = nodes.new("ShaderNodeTexImage")
                    mat_name = material.name
                    if "." in mat_name:
                        mat_name = mat_name[:mat_name.find(".")]
                    mat_name = mat_name.replace("_", "")
                    # remove all digits from the string
                    mat_name = ''.join([i for i in mat_name if not i.isdigit()])
                    image_paths = glob.glob(os.path.join(self._texture_folder, mat_name, "*"))
                    if not image_paths:
                        image_paths = glob.glob(os.path.join(self._texture_folder, "unknown", "*"))
                        print("Warning: The material {} was not found use unknown instead.".format(mat_name))
                    image_path = random.choice(image_paths)
                    if os.path.exists(image_path):
                        texture_node.image = bpy.data.images.load(image_path, check_existing=True)
                    else:
                        raise Exception("No image was found for this entity: {}, material name: {}".format(obj.name, mat_name))
                    links.new(texture_node.outputs["Color"], principled_bsdf.inputs["Base Color"])
                    if "lamp" in mat_name or "ceiling" in mat_name:
                        mix_node = nodes.new(type='ShaderNodeMixShader')
                        Utility.insert_node_instead_existing_link(links, principled_bsdf.outputs['BSDF'], mix_node.inputs[2], mix_node.outputs['Shader'], output_node.inputs['Surface'])

                        # The light path node returns 1, if the material is hit by a ray coming from the camera, else it returns 0.
                        # In this way the mix shader will use the principled shader for rendering the color of the lightbulb itself, while using the emission shader for lighting the scene.
                        lightPath_node = nodes.new(type='ShaderNodeLightPath')
                        links.new(lightPath_node.outputs['Is Camera Ray'], mix_node.inputs['Fac'])

                        emission_node = nodes.new(type='ShaderNodeEmission')
                        if "lamp" in mat_name:
                            links.new(texture_node.outputs["Color"], emission_node.inputs["Color"])

                        if "lamp" in mat_name:
                            # If the material corresponds to a lampshade
                            emission_node.inputs['Strength'].default_value = self.config.get_float("lampshade_emission_strength", 15)
                        elif "ceiling" in mat_name:
                            # If the material corresponds to a ceiling
                            emission_node.inputs['Strength'].default_value = self.config.get_float("ceiling_emission_strength", 2)

                        links.new(emission_node.outputs["Emission"], mix_node.inputs[1])
        for obj in loaded_objects:
            obj_name = obj.name
            if "." in obj_name:
                obj_name = obj_name[:obj_name.find(".")]
            obj_name = obj_name.lower()
            if "wall" in obj_name or "floor" in obj_name or "ceiling" in obj_name:
                # set the shading of all polygons to flat
                for poly in obj.data.polygons:
                    poly.use_smooth = False

    def _set_category_ids(self, loaded_objects):
        if self._category_labels:

            for obj in loaded_objects:
                obj_name = obj.name
                if "." in obj_name:
                    obj_name = obj_name[:obj_name.find(".")]
                if obj_name in self._category_labels:
                    obj["category_id"] = self._category_labels[obj_name]
                elif obj_name[-1] == "s" and obj_name[:-1] in self._category_labels:
                    obj["category_id"] = self._category_labels[obj_name[:-1]]
                elif "painting" in obj_name:
                    obj["category_id"] = self._category_labels["picture"]
                else:
                    print("This object was not specified: {} use objects for it.".format(obj_name))
                    obj["category_id"] = self._category_labels["other-structure".lower()]





