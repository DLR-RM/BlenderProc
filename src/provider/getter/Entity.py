import json
import re
from random import sample

import bpy
import mathutils

from src.main.Provider import Provider
from src.utility.Config import Config


class Entity(Provider):
    """
    Returns a list of objects that comply with defined conditions.

    Example 1: Return a list of objects that match a name pattern.

    .. code-block:: yaml

        {
          "provider": "getter.Entity",
          "conditions": {
            "name": "Suzanne.*"
          }
        }

    Example 2: Returns the first object to: {match the name pattern "Suzanne", AND to be of a MESH type},
    OR {match the name pattern, AND have a certain value of a cust. prop}
    OR {be inside a bounding box defined by a min and max points}
    OR {have a Z position in space greater than -1}

    .. code-block:: yaml

        {
          "provider": "getter.Entity",
          "index": 0,
          "conditions": [
          {
            "name": "Suzanne",
            "type": "MESH"
          },
          {
            "name": "Cube.*",
            "cp_category": "is_cube"
          },
          {
            "cf_inside": {
            "min": "[-5, -5, -5]",
            "max": "[5, 5, 5]"
            }
          },
          {
            "cf_inside": {
              "z_min": -1,
            }
          }
          ]
        }

    Example 3: Returns two random objects of MESH type.

    .. code-block:: yaml

        {
          "provider": "getter.Entity",
          "random_samples": 2,
          "conditions": {
            "type": "MESH"
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
          - Any value to set.
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

    **Custom functions**

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cf_{inside,outside}
          - Returns objects that lies inside/outside of a bounding box or with a specific coordinate component >,<
            than a value. 
          - dict
        * - cf_{inside,outside}/(min,max)
          - min and max pair defines a bounding box used for a check. cannot be mixed with /[xyz]_{min,max}
            configuration. 
          - list ([x, y, z])
        * - cf_{inside,outside}/[xyz]_(min,max)
          - Alternative syntax. Defines a hyperplane. Missing arguments extend the bounding box to infinity in that direction.    
          - float
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def perform_and_condition_check(self, and_condition, objects):
        """ Checks all objects in the scene if all given conditions are true for an object, it is added to the list.

        :param and_condition: Given conditions. Type: dict.
        :param objects: Objects, that are already in the return list. Type: list.
        :return: Objects that fulfilled given conditions. Type: list.
        """
        new_objects = []
        # through every object
        for obj in bpy.context.scene.objects:
            # if object is in list, skip it
            if obj in objects:
                continue
            select_object = True
            # run over all conditions and check if any one of them holds, if one does not work -> go to next obj
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

                # check if an attribute with this name exists and the key was not a requested custom property
                if hasattr(obj, key) and not requested_custom_property:
                    # check if the type of the value of attribute matches desired
                    if isinstance(getattr(obj, key), type(value)):
                        new_value = value
                    # if not, try to enforce some mathutils-specific type
                    else:
                        if isinstance(getattr(obj, key), mathutils.Vector):
                            new_value = mathutils.Vector(value)
                        elif isinstance(getattr(obj, key), mathutils.Euler):
                            new_value = mathutils.Euler(value)
                        elif isinstance(getattr(obj, key), mathutils.Color):
                            new_value = mathutils.Color(value)
                        # raise an exception if it is none of them
                        else:
                            raise Exception("Types are not matching: %s and %s !"
                                            % (type(getattr(obj, key)), type(value)))
                    # or check for equality
                    if not ((isinstance(getattr(obj, key), str) and re.fullmatch(value, getattr(obj, key)) is not None)
                            or getattr(obj, key) == new_value):
                        select_object = False
                        break
                # check if a custom property with this name exists
                elif key in obj and requested_custom_property:
                    # check if the type of the value of such custom property matches desired
                    if isinstance(obj[key], type(value)) or (isinstance(obj[key], int) and isinstance(value, bool)):
                        # if is a string and if the whole string matches the given pattern
                        if not ((isinstance(obj[key], str) and re.fullmatch(value, obj[key]) is not None) or
                                obj[key] == value):
                            select_object = False
                            break
                    # raise an exception if not
                    else:
                        raise Exception("Types are not matching: {} and {} for key: {}".format(type(obj[key]),
                                                                                               type(value), key))
                elif requested_custom_function and any([key == "inside", key == "outside"]):
                    conditions = Config(value)
                    if conditions.has_param("min") and conditions.has_param("max"):
                        if any(conditions.has_param(key) for key in
                               ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"]):
                            raise RuntimeError("An inside/outside condition cannot mix the min/max vector syntax with "
                                               "the x_min/x_max/y_min/... syntax.")

                        bb_min = conditions.get_vector3d("min")
                        bb_max = conditions.get_vector3d("max")
                        is_inside = all(bb_min[i] < obj.location[i] < bb_max[i] for i in range(3))
                    else:
                        if any(conditions.has_param(key) for key in ["min", "max"]):
                            raise RuntimeError("An inside/outside condition cannot mix the min/max syntax with "
                                               "the x_min/x_max/y_min/... syntax.")
                        is_inside = True
                        for axis_index in range(3):
                            axis_name = "xyz"[axis_index]
                            for direction in ["min", "max"]:
                                key_name = "{}_{}".format(axis_name, direction)
                                if key_name in value:
                                    real_position = obj.location[axis_index]
                                    border_position = float(value[key_name])
                                    if (direction == "max" and real_position > border_position) or (
                                            direction == "min" and real_position < border_position):
                                        is_inside = False

                    if (key == "inside" and not is_inside) or (key == "outside" and is_inside):
                        select_object = False
                        break
                else:
                    select_object = False
                    break
            if select_object:
                new_objects.append(obj)
        return new_objects

    def _get_conditions_as_string(self):
        """
        Returns the used conditions as neatly formatted string
        :return: str: containing the conditions
        """
        conditions = self.config.get_raw_dict('conditions')
        text = json.dumps(conditions, indent=2, sort_keys=True)
        def add_indent(t): return "\n".join(" " * len("Exception: ") + e for e in t.split("\n"))
        return add_indent(text)

    def run(self):
        """ Processes defined conditions and compiles a list of objects.

        :return: List of objects that met the conditional requirement. Type: list.
        """
        conditions = self.config.get_raw_dict('conditions')

        # the list of conditions is treated as or condition
        if isinstance(conditions, list):
            objects = []
            # each single condition is treated as and condition
            for and_condition in conditions:
                objects.extend(self.perform_and_condition_check(and_condition, objects))
        else:
            # only one condition was given, treat it as and condition
            objects = self.perform_and_condition_check(conditions, [])

        random_samples = self.config.get_int("random_samples", 0)
        has_index = self.config.has_param("index")

        if has_index and random_samples:
            raise RuntimeError("Please, define only one of two: `index` or `random_samples`.")
        elif has_index:
            objects = [objects[self.config.get_int("index")]]
        elif random_samples:
            objects = sample(objects, k=min(random_samples, len(objects)))

        check_if_return_is_empty = self.config.get_bool("check_empty", False)
        if check_if_return_is_empty and not objects:
            raise Exception(f"There were no objects selected with the following "
                            f"condition: \n{self._get_conditions_as_string()}")

        return objects
