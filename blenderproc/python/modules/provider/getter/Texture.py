import json
import re
from random import sample

import mathutils

from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.utility.BlenderUtility import get_all_textures


class Texture(Provider):
    """
    Returns a list of textures in accordance with defined conditions.

    Example 1: Return a list of textures that match a name pattern.

    .. code-block:: yaml

        {
          "provider": "getter.Texture",
          "conditions": {
            "name": "ct_.*"
          }
        }

    Example 2: Returns the first texture to: {match the name pattern, AND to have nodes use enabled },
    OR {match anothername pattern, AND have a certain value of a cust. prop}

    .. code-block:: yaml

        {
          "provider": "getter.Texture",
          "index": 0,
          "conditions": [
          {
            "name": "ct_1.*",
            "use_nodes": True
          },
          {
            "name": "ct_2.*",
            "cp_type": "custom"
          }]
        }

    Example 3: Returns two random textures with a certain value of a custom property.

    .. code-block:: yaml

        {
          "provider": "getter.Texture",
          "random_samples": 2,
          "conditions": {
            "cp_type": "custom"
          }
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - conditions
          - List of dicts/a dict of entries of format {attribute_name: attribute_value}. Entries in a dict are
            conditions connected with AND, if there multiple dicts are defined (i.e. 'conditions' is a list of
            dicts, each cell is connected by OR. 
          - list/dict
        * - conditions/attribute_name
          - Name of any valid object's attribute, custom property, or custom function. Any given attribute_value of
            the type string will be treated as a REGULAR EXPRESSION. Also, any attribute_value for a custom property
            can be a string/int/bool/float, while only attribute_value for valid attributes of objects can be a bool
            or a list (mathutils.Vector, mathurils.Color and mathutils.Euler are covered by the 'list' type). " In
            order to specify, what exactly one wants to look for: For attribute: key of the pair must be a valid
            attribute name. For custom property: key of the pair must start with `cp_` prefix. For calling custom
            function: key of the pair must start with `cf_` prefix. See table below for supported custom functions.
          - string
        * - conditions/attribute_value
          - Any value to set. .
          - string, list/Vector, int, bool or float
        * - index
          - If set, after the conditions are applied only the entity with the specified index is returned. 
          - int
        * - random_samples
          - If set, this Provider returns random_samples objects from the pool of selected ones. Define index or
            random_samples property, only one is allowed at a time. Default: 0.
          - int
        * - check_empty
          - If this is True, the returned list can not be empty, if it is empty an error will be thrown. Default: False.
          - bool
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        conditions = self.config.get_raw_dict('conditions')

        if isinstance(conditions, list):
            textures = []
            # each single condition is treated as and condition
            for and_condition in conditions:
                textures.extend(self.perform_and_condition_check(and_condition, textures))
        else:
            # only one condition was given, treat it as and condition
            textures = self.perform_and_condition_check(conditions, [])

        random_samples = self.config.get_int("random_samples", 0)
        has_index = self.config.has_param("index")

        if has_index and not random_samples:
            textures = [textures[self.config.get_int("index")]]
        elif random_samples and not has_index:
            textures = sample(textures, k=min(random_samples, len(textures)))
        elif has_index and random_samples:
            raise RuntimeError("Please, define only one of two: `index` or `random_samples`.")

        check_if_return_is_empty = self.config.get_bool("check_empty", False)
        if check_if_return_is_empty and not textures:
            raise Exception(f"There were no materials selected with the following "
                            f"condition: \n{self._get_conditions_as_string()}")

        return textures

    def _get_conditions_as_string(self):
        """
        Returns the used conditions as neatly formatted string
        :return: str: containing the conditions
        """
        conditions = self.config.get_raw_dict('conditions')
        text = json.dumps(conditions, indent=2, sort_keys=True)
        # Add indent
        text = "\n".join(" " * len("Exception: ") + e for e in text.split("\n"))
        return text

    @staticmethod
    def perform_and_condition_check(and_condition, textures, used_textures_to_check=None):
        """ Checks for all textures and if all given conditions are true, collects them in the return list.

        :param and_condition: Given conditions. Type: dict.
        :param textures: Textures, that are already in the return list. Type: list.
        :param used_textures_to_check: Textures to perform the check on. Type: list. Default: all materials
        :return: Textures that comply with given conditions. Type: list.
        """
        new_textures = []
        if used_textures_to_check is None:
            used_textures_to_check = get_all_textures()

        for texture in used_textures_to_check:
            if texture in new_textures or texture in textures:
                continue

            select_texture = True
            for key, value in and_condition.items():
                # check if the key is a requested custom property
                requested_custom_property = False
                #requested_custom_function = False
                if key.startswith('cp_'):
                    requested_custom_property = True
                    key = key[3:]
                if key.startswith('cf_'):
                    #requested_custom_function = True
                    #key = key[3:]
                    raise RuntimeError("Custom functions for texture objects are yet to be implemented!")
                if hasattr(texture, key) and not requested_custom_property:
                    # check if the type of the value of attribute matches desired
                    if isinstance(getattr(texture, key), type(value)):
                        new_value = value
                    # if not, try to enforce some mathutils-specific type
                    else:
                        if isinstance(getattr(texture, key), mathutils.Vector):
                            new_value = mathutils.Vector(value)
                        elif isinstance(getattr(texture, key), mathutils.Euler):
                            new_value = mathutils.Euler(value)
                        elif isinstance(getattr(texture, key), mathutils.Color):
                            new_value = mathutils.Color(value)
                        # raise an exception if it is none of them
                        else:
                            raise Exception("Types are not matching: %s and %s !"
                                            % (type(getattr(texture, key)), type(value)))
                    # or check for equality
                    if not ((isinstance(getattr(texture, key), str) and
                             re.fullmatch(value, getattr(texture, key)) is not None)
                            or getattr(texture, key) == new_value):
                        select_texture = False
                        break
                    # check if a custom property with this name exists
                elif key in texture and requested_custom_property:
                    # check if the type of the value of such custom property matches desired
                    if isinstance(texture[key], type(value)) or (
                            isinstance(texture[key], int) and isinstance(value, bool)):
                        # if it is a string and if the whole string matches the given pattern
                        if not ((isinstance(texture[key], str) and re.fullmatch(value, texture[key]) is not None) or
                                texture[key] == value):
                            select_texture = False
                            break
                    else:
                        # raise an exception if not
                        raise Exception("Types are not matching: {} and {} !".format(type(texture[key]), type(value)))
                else:
                    select_texture = False
                    break

            if select_texture:
                new_textures.append(texture)

        return new_textures
