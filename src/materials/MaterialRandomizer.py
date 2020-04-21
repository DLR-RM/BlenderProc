
import numpy as np

from src.main.Module import Module
from src.utility.BlenderUtility import get_all_mesh_objects, get_all_materials


class MaterialRandomizer(Module):
    """
    Randomizes the materials for the selected objects, the default is all.
    The amount of randomization depends on the randomization level (0 - 1).
    Randomization level => Expected fraction of objects for which the texture should be randomized.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "randomization_level", "Level of randomization, greater the value greater the number of objects for which the
                               materials are randomized. Allowed values are [0-1], default: 0.2, Type: Float"
       "manipulated_objects", "Selector (getter.Object), to select all objects which materials should be changed,
                               by default: all"
       "materials_to_replace_with", "Selector (getter.Materials) a list of materials to use for the replacement
                                  by default: all"
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.randomization_level = 0
        self._objects_to_manipulate = []
        self._materials_to_replace_with = []

    def run(self):
        """
            Walks over all objects and randomly switches the materials with the materials_to_replace_with
        """
        self.randomization_level = self.config.get_float("randomization_level", 0.2)
        self._objects_to_manipulate = self.config.get_list('manipulated_objects', get_all_mesh_objects())
        self._materials_to_replace_with = self.config.get_list("materials_to_replace_with", get_all_materials())
        # walk over all objects
        for obj in self._objects_to_manipulate:
            if hasattr(obj, 'material_slots'):
                # walk over all materials
                for material in obj.material_slots:
                    if np.random.uniform(0, 1) <= self.randomization_level:
                        # select a random material to replace the old one with
                        material.material = np.random.choice(self._materials_to_replace_with)

