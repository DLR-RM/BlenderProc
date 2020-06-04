import numpy as np

from src.main.Module import Module
from src.utility.BlenderUtility import get_all_mesh_objects, get_all_materials
from src.provider.getter.Material import Material

class MaterialRandomizer(Module):
    """ Randomizes the materials for the selected objects.

        Example 1: For all of the objects in the scene assign a random existing material with probability of 50%.

        {
          "module": "materials.MaterialRandomizer",
          "config": {
            "randomization_level": 0.5,
          }
        }

        Example 2: For all of the objects matching the name pattern with probability of 100% set one randomly chosen
                   material from those which match the custom property value .

        {
          "module": "materials.MaterialRandomizer",
          "config": {
            "randomization_level": 1,
            "mode": "once_for_all",
            "manipulated_objects": {
              "provider": "getter.Entity",
              "conditions": {
                "name": "Plane.*"
              }
            },
            "materials_to_replace_with": {
              "provider": "getter.Material",
              "conditions": {
                "cp_is_cc_texture": True
              }
            }
          }
        }

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "randomization_level", "Expected fraction of the selected objects for which the texture should be randomized. "
                               "Type: float. Range: [0, 1]. Default: 0.2."
        "manipulated_objects", "Objects to have their material randomized. Type: Provider. Default: all mesh objects."
        "materials_to_replace_with", "Materials to participate in randomization. Type: Provider. Default: all materials."
        "mode", "Mode of operation. Type: string. Default: "once_for_each".
                "Available: 'once_for_each' (sampling the "material once for each object),"
                "'once_for_all' (sampling once for all of the objects)."
        "obj_materials_cond_to_be_replaced", "A dict of materials and corresponding conditions making it possible to"
                                             "only replace materials with certain properties. These are similiar to"
                                             "the conditions mentioned in the material_getter. Type: dict. Default: {}."
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.randomization_level = 0
        self._objects_to_manipulate = []
        self._materials_to_replace_with = []

    def run(self):
        """ Randomizes materials for selected objects.
            1. For each object assign a randomly chosen material from the pool.
        """
        self.randomization_level = self.config.get_float("randomization_level", 0.2)
        self._objects_to_manipulate = self.config.get_list('manipulated_objects', get_all_mesh_objects())
        self._materials_to_replace_with = self.config.get_list("materials_to_replace_with", get_all_materials())
        self._obj_materials_cond_to_be_replaced = self.config.get_raw_dict("obj_materials_to_be_replaced", {})
        op_mode = self.config.get_string("mode", "once_for_each")

        # if there were no materials selected throw an exception
        if not self._materials_to_replace_with:
            print("Warning: No materials selected inside of the MaterialRandomizer!")
            return

        if op_mode == "once_for_all":
            random_material = np.random.choice(self._materials_to_replace_with)

        # walk over all objects
        for obj in self._objects_to_manipulate:
            if hasattr(obj, 'material_slots'):
                # walk over all materials
                for material in obj.material_slots:
                    use_mat = True
                    if self._obj_materials_cond_to_be_replaced:
                        use_mat = len(Material.perform_and_condition_check(self._obj_materials_cond_to_be_replaced, [], [material.material])) == 1
                    if use_mat:
                        if np.random.uniform(0, 1) <= self.randomization_level:
                            if op_mode == "once_for_each":
                                random_material = np.random.choice(self._materials_to_replace_with)
                            # select a random material to replace the old one with
                            material.material = random_material
