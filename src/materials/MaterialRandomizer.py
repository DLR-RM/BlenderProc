from src.main.Module import Module
import bpy
from src.utility.Utility import Utility
import numpy as np


class MaterialRandomizer(Module):

    """
    Randomizes the materials for the objects of the scene. The amount of randomization depends
    on the randomization level (0 - 1).
    Randomization level => Expected fraction of objects for which the texture should be randomized

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "randomization_level", "Level of randomization, greater the value greater the number of objects for which the
                              materials are randomized. Allowed values are [0-1]"
       "randomize_textures_only", "True or False. When True, only materials that have texture(image)
                                   will be randomly assigned a material
       "output_textures_only", "True or False. When True, the set of materials used for the sampling will consist of
                               only materials which have texture(image) in it."

    """

    def __init__(self, config):

        Module.__init__(self, config)
        self.randomization_level = self.config.get_float("randomization_level", 0.2)
        self.randomize_textures_only = self.config.get_float("randomize_textures_only", False)
        self.output_textures_only = self.config.get_float("output_textures_only", True)
        self.scene_materials = []

    def run(self):

        self._store_all_materials()
        if self.scene_materials:
            self._randomize_materials_in_scene()
        else:
            print("Warning there are no materials, which can be switched!")

    def _randomize_materials_in_scene(self):

        """
        Randomizes the materials of objects in a loaded scene
        """

        for obj in bpy.context.scene.objects:
            self._randomize_material_for_obj(obj)

    def _randomize_material_for_obj(self, obj):

        for m in obj.material_slots:
            # Check if materials without texture should be randomized
            if self.randomize_textures_only:
                # Check if the material has a texture image
                nodes = m.material.node_tree.nodes

                if Utility.get_nodes_with_type(nodes, "TexImage"):
                    self._pick_assign_random_material(m)
            else:
                self._pick_assign_random_material(m)

    def _pick_assign_random_material(self, m):

        """
        For the given material slot with randomization_level probability assigns a random
        material(with or without texture depending on the value of output_textures_only) from the scene

        :param m: Material slot for which material should be randomized
        """

        if np.random.uniform(0, 1) <= self.randomization_level:
            random_index = np.random.random_integers(0, len(self.scene_materials) - 1)
            m.material = self.scene_materials[random_index]

    def _store_all_materials(self):

        """
        Stores all available materials(with or without textures depending on output_textures_only) from the scene
        """

        for obj in bpy.context.scene.objects:
            for m in obj.material_slots:
                if self.output_textures_only:
                    # check if any texture nodes are in this material, no check if they are connected to the output
                    if Utility.get_nodes_with_type(m.material.node_tree.nodes, 'TexImage'):
                        self.scene_materials.append(m.material.copy())
                else:
                    self.scene_materials.append(m.material.copy())
