import re
from random import sample

import mathutils

from src.main.Provider import Provider
from src.utility.BlenderUtility import get_all_materials
from src.utility.Utility import Utility


class Material(Provider):
    """
    Returns a list of materials that comply with defined conditions.

    Example 1: Return materials matching a name pattern.

    .. code-block:: yaml

        {
          "provider": "getter.Material",
          "conditions": {
            "name": "wood.*"
          }
        }

    Example 2: Return all materials matching a name pattern which also have exactly two textures used.

    .. code-block:: yaml

        {
          "provider": "getter.Material",
          "conditions": {
            "name": "wood.*",
            "cf_texture_amount_eq": "2"
          }
        }

    Example 3: Return all materials matching a name pattern which also have two or more textures used.

    .. code-block:: yaml

        {
          "provider": "getter.Material",
          "conditions": {
            "name": "wood.*",
            "cf_texture_amount_min": "2"
          }
        }

    Example 4: Return all materials which: {match the name pattern 'wood.*' AND have two or less textures used}
                                            OR {match the name pattern 'tile.*'}

    .. code-block:: yaml

        {
          "provider": "getter.Material",
          "conditions": [
          {
            "name": "wood.*",
            "cf_texture_amount_max": "2"
          },
          {
            "name: "tile.*"
          }
          ]
        }

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "conditions", "List of dicts/a dict of entries of format {attribute_name: attribute_value}. Entries in a dict "
                      "are conditions connected with AND, if there multiple dicts are defined (i.e. 'conditions' is a "
                      "list of dicts, each cell is connected by OR. Type: list/dict."
        "conditions/attribute_name", "Name of any valid material's attribute, custom property, or custom function. Any "
                                     "given attribute_value of the type string will be treated as a REGULAR EXPRESSION. "
                                     "Type: string. "
                                     "In order to specify, what exactly one wants to look for: "
                                     "For attribute: key of the pair must be a valid attribute name. "
                                     "For custom property: key of the pair must start with `cp_` prefix. "
                                     "For calling custom function: key of the pair must start with `cf_` prefix. See "
                                     "table below for supported custom functions."
        "conditions/attribute_value", "Any value to set. Type: string, int, bool or float, list/Vector."
        "index", "If set, after the conditions are applied only the entity with the specified index is returned. "
                 "Type: int."
        "random_samples", "If set, this Provider returns random_samples objects from the pool of selected ones. Define "
                          "index or random_samples property, only one is allowed at a time. Type: int. Default: False."

    **Custom functions**

    .. csv-table::
        :header: "Parameter", "Description"

        "cf_texture_amount_{min,max,eq}", "Returns materials that have a certain amount of texture nodes inside of the "
                                          "material. Suffix 'min' = less nodes or equal than specified, 'max' = at "
                                          "least as many or 'eq' = for this exact amount of textures nodes. Type: int."
        "cf_principled_bsdf_amount_{min,max,eq}", "Returns materials that have a certain amount of principled bsdf"
                                                  "nodes inside of the material. Suffix 'min' = less nodes or equal"
                                                  "than specified, 'max' = at least as many or 'eq' = for this exact"
                                                  "amount of principled bsdf nodes. Type: int."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    @staticmethod
    def perform_and_condition_check(and_condition, materials, used_materials_to_check=None):
        """ Checks for all materials in the scene if all given conditions are true, collects them in the return list.

        :param and_condition: Given conditions. Type: dict.
        :param materials: Materials, that are already in the return list. Type: list.
        :param used_materials_to_check: a list of materials to perform the check on. Type: list. Default: all materials
        :return: Materials that fulfilled given conditions. Type: list.
        """
        new_materials = []
        if used_materials_to_check is None:
            used_materials_to_check = get_all_materials()

        # through every material
        for material in used_materials_to_check:
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
                            value = int(value)
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
                    elif key.startswith("principled_bsdf_amount_"):
                        if material.use_nodes:
                            value = int(value)
                            nodes = material.node_tree.nodes
                            principled = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
                            amount_of_principled_bsdf_nodes = len(principled) if principled is not None else 0
                            if "min" in key:
                                if not (amount_of_principled_bsdf_nodes >= value):
                                    select_material = False
                                    break
                            elif "max" in key:
                                if not (amount_of_principled_bsdf_nodes <= value):
                                    select_material = False
                                    break
                            elif "eq" in key:
                                if not (amount_of_principled_bsdf_nodes == value):
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
        """ Processes defined conditions and compiles a list of materials.

        :return: List of materials that met the conditional requirement. Type: list.
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

        random_samples = self.config.get_int("random_samples", 0)
        has_index = self.config.has_param("index")

        if has_index and not random_samples:
            materials = [materials[self.config.get_int("index")]]
        elif random_samples and not has_index:
            materials = sample(materials, k=min(random_samples, len(materials)))
        elif has_index and random_samples:
            raise RuntimeError("Please, define only one of two: `index` or `random_samples`.")

        return materials
