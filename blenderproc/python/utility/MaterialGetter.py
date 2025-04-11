""" This module provides functions to filter materials. """

import re

import mathutils

from blenderproc.python.utility.BlenderUtility import get_all_materials
from blenderproc.python.utility.Utility import Utility


class MaterialGetter:
    """ Filters materials. """

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
            if material in new_materials or material in materials or material is None:
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
                if hasattr(material, key) and not requested_custom_property and not requested_custom_function:
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
                            raise Exception(f"Types are not matching: {type(getattr(material, key))} "
                                            "and {type(value)} !")
                    # or check for equality
                    if not ((isinstance(getattr(material, key), str) and
                            re.fullmatch(value, getattr(material, key)) is not None)
                            or getattr(material, key) == new_value):
                        select_material = False
                        break
                # check if a custom property with this name exists
                elif key in material and requested_custom_property:
                    # check if the type of the value of such custom property matches desired
                    if isinstance(material[key], type(value)) or (isinstance(material[key], int)
                                                                  and isinstance(value, bool)):
                        # if it is a string and if the whole string matches the given pattern
                        if not ((isinstance(material[key], str) and re.fullmatch(value, material[key]) is not None) or
                                material[key] == value):
                            select_material = False
                            break
                    else:
                        # raise an exception if not
                        raise Exception(f"Types are not matching: {type(material[key])} and {type(value)} !")
                elif requested_custom_function:
                    if key.startswith("texture_amount_"):
                        if material.use_nodes:
                            value = int(value)
                            nodes = material.node_tree.nodes
                            texture_nodes = Utility.get_nodes_with_type(nodes, "TexImage")
                            amount_of_texture_nodes = len(texture_nodes) if texture_nodes is not None else 0
                            if "min" in key:
                                if not amount_of_texture_nodes >= value:
                                    select_material = False
                                    break
                            elif "max" in key:
                                if not amount_of_texture_nodes <= value:
                                    select_material = False
                                    break
                            elif "eq" in key:
                                if not amount_of_texture_nodes == value:
                                    select_material = False
                                    break
                            else:
                                raise Exception(f"This type of key is unknown: {key}")
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
                                if not amount_of_principled_bsdf_nodes >= value:
                                    select_material = False
                                    break
                            elif "max" in key:
                                if not amount_of_principled_bsdf_nodes <= value:
                                    select_material = False
                                    break
                            elif "eq" in key:
                                if not amount_of_principled_bsdf_nodes == value:
                                    select_material = False
                                    break
                            else:
                                raise Exception(f"This type of key is unknown: {key}")
                        else:
                            select_material = False
                            break
                    elif key.startswith("principled_bsdf_"):  # must be after the amount check
                        # This custom function can check the value of a certain Principled BSDF shader input.
                        # For example this can be used to avoid using materials, which have an Alpha Texture by
                        # adding they key: `"cf_principled_bsdf_Alpha_eq": 1.0`
                        if material.use_nodes:
                            value = float(value)
                            # first check if there is only one Principled BSDF node in the material
                            nodes = material.node_tree.nodes
                            principled = Utility.get_nodes_with_type(nodes, "BsdfPrincipled")
                            amount_of_principled_bsdf_nodes = len(principled) if principled is not None else 0
                            if amount_of_principled_bsdf_nodes != 1:
                                select_material = False
                                break
                            principled = principled[0]
                            # then extract the input name from the key, for the Alpha example: `Alpha`
                            extracted_input_name = key[len("principled_bsdf_"):key.rfind("_")]
                            # check if this key exists, else throw an error
                            if extracted_input_name not in principled.inputs:
                                raise Exception("Only valid inputs of a principled node are allowed: "
                                                f"{extracted_input_name} in: {key}")
                            # extract this input value
                            used_value = principled.inputs[extracted_input_name]
                            # if this input value is not a default value it will be connected via the links
                            if len(used_value.links) > 0:
                                select_material = False
                                break
                            # if no link is found check the default value
                            used_value = used_value.default_value
                            # compare the given value to the default value
                            if key.endswith("min"):
                                if not used_value >= value:
                                    select_material = False
                                    break
                            elif key.endswith("max"):
                                if not used_value <= value:
                                    select_material = False
                                    break
                            elif key.endswith("eq"):
                                if not used_value == value:
                                    select_material = False
                                    break
                            else:
                                raise Exception(f"This type of key is unknown: {key}")
                        else:
                            select_material = False
                            break
                    elif key == "use_materials_of_objects":
                        objects = Utility.build_provider_based_on_config(value).run()
                        found_material = False
                        # iterate over all selected objects
                        for obj in objects:
                            # check if they have materials
                            if hasattr(obj, "material_slots"):
                                for mat_slot in obj.material_slots:
                                    # if the material is the same as the currently checked one
                                    if mat_slot.material == material:
                                        found_material = True
                                        break
                            if found_material:
                                break
                        if not found_material:
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
