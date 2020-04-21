import bpy
import mathutils
import re

from src.utility.Utility import Utility
from src.utility.BlenderUtility import get_all_materials
from src.main.Provider import Provider

class Material(Provider):
    """
    Returns a list of materials in accordance to a condition.
    Specify a desired condition in the format {attribute_name: attribute_value}

    The usual conditions might be:
    1.

    "selector": {
      "provider": "getter.Material",
      "conditions": {"name": "wood.*"}
    }

    Here all materials which start with wood are selected.

    2.

    "selector": {
      "provider": "getter.Material",
      "conditions": {
        "name": "wood.*",
        "cf_texture_amount_eq": "2"
      }
    }

    In this example again all materials where the name starts with wood are selected and where the material
    has exactly two texture used. All the elements

    3.

    "selector": {
      "provider": "getter.Material",
      "conditions": {
        "name": "wood.*",
        "cf_texture_amount_min": "2"
      }
    }

    The only difference to 2. is that now the amount of textures must be equal or higher than 2, this option also
    exists with "cf_texture_amount_max".

    4.

    It is also possible to use several OR conditions, by using a list of dicts:

    "selector": {
      "provider": "getter.Material",
      "conditions": [
        {
          "name": "wood.*",
          "cf_texture_amount_min": "2"
        },
        { "name: "tile.*" }
      ]
    }

    This would include all materials which either start with wood or tile. The wood materials also need at least 2
    texture image nodes.

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

    "conditions", "List of dicts/a dict of entries of format {attribute_name: attribute_value}. Entries in a dict are "
                  "conditions connected with AND, if there multiple dicts are defined (i.e. 'conditions' is a list of "
                  "dicts, each cell is connected by OR. Type: list of dicts/dict."
    "conditions/attribute_name", "Name of any valid material's attribute or custom function. Type: string."
                                "In order to specify, what exactly one wants to look for (e.g. attribute's/c.p. value, etc.): "
                                "For attribute: key of the pair must be a valid attribute name. "
                                "For custom property: key of the pair must start with `cp_` prefix. "
                                "For calling custom function: key of the pair must start with `cf_` prefix. See table "
                                "below for supported cf names."
    "conditions/attribute_value", "Any value to set. Types: string, int, bool or float, list/Vector/Euler/Color."
    "index", "If set, after the conditions are applied only the entity with the specified index is returned. Type: int."

    """


    def __init__(self, config):
        Provider.__init__(self, config)

    def perform_and_condition_check(self, and_condition, materials):
        """
        Checks for all materials in the scene if all given conditions are true, collects them in the return list
        See class description on how to set up AND and OR connections.
        :param and_condition: Given dictionary with conditions
        :param materials: list of materials, which already have been used
        :return: list of materials, which full fill the conditions
        """
        new_materials = []
        # through every material
        for material in get_all_materials():
            if material in new_materials or material in materials:
                continue

            select_material = True
            for key, value in and_condition.items():
                # check if the key is a requested custom property
                requested_custom_property = False
                requested_custom_function = False
                if key.startswith('cp_'):
                    requested_custom_property = True
                    key = key[3:]
                if key.startswith('cf_'):
                    requested_custom_function = True
                    key = key[3:]
                if hasattr(material, key) and not requested_custom_property:
                    # check if the type of the value of attribute matches desired
                    if isinstance(getattr(material, key), type(value)):
                        new_value = value
                    # if not, try to enforce some mathutils-specific type
                    else:
                        if isinstance(getattr(material, key), mathutils.Vector):
                            new_value = mathutils.Vector(value)
                        elif isinstance(getattr(material, key), mathutils.Euler):
                            new_value = mathutils.Euler(value)
                        elif isinstance(getattr(material, key), mathutils.Color):
                            new_value = mathutils.Color(value)
                        # raise an exception if it is none of them
                        else:
                            raise Exception("Types are not matching: %s and %s !"
                                            % (type(getattr(material, key)), type(value)))
                    # or check for equality
                    if not ((isinstance(getattr(material, key), str) and re.fullmatch(value, getattr(material, key)) is not None)
                            or getattr(material, key) == new_value):
                        select_material = False
                        break
                # check if a custom property with this name exists
                elif key in material and requested_custom_property:
                    # check if the type of the value of such custom property matches desired
                    if isinstance(material[key], type(value)) or (isinstance(material[key], int) and isinstance(value, bool)):
                        # if it is a string and if the whole string matches the given pattern
                        if not ((isinstance(material[key], str) and re.fullmatch(value, material[key]) is not None) or
                                material[key] == value):
                            select_material = False
                            break
                    else:
                        # raise an exception if not
                        raise Exception("Types are not matching: {} and {} !".format(type(material[key]), type(value)))
                elif requested_custom_function:
                    if key.startswith("texture_amount_"):
                        if material.use_nodes:
                            nodes = material.node_tree.nodes
                            texture_nodes = Utility.get_nodes_with_type(nodes, "TexImage")
                            amount_of_texture_nodes = len(texture_nodes) if texture_nodes is not None else 0
                            if "min" in key:
                                if not (amount_of_texture_nodes >= value):
                                    select_material = False
                                    break
                            elif "max" in key:
                                if not (amount_of_texture_nodes <= value):
                                    select_material = False
                                    break
                            elif "eq" in key:
                                if not (amount_of_texture_nodes == value):
                                    select_material = False
                                    break
                            else:
                                raise Exception("This type of key is unknown: {}".format(key))
                        else:
                            select_material = False
                            break
                    else:
                        select_material = False
                        break
                else:
                    select_material = False
                    break
            if select_material:
                new_materials.append(material)
        return new_materials

    def run(self):
        """
        :return: List of materials that met the conditional requirement.
        """
        conditions = self.config.get_raw_dict('conditions')

        # the list of conditions is treated as or condition
        if isinstance(conditions, list):
            materials = []
            # each single condition is treated as and condition
            for and_condition in conditions:
                materials.extend(self.perform_and_condition_check(and_condition, materials))
        else:
            # only one condition was given, treat it as and condition
            materials = self.perform_and_condition_check(conditions, [])

        return materials
