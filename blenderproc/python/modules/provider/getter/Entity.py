import json
from random import sample

import bpy
import mathutils

from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.types.EntityUtility import convert_to_entities
import blenderproc.python.filter.Filter as Filter
import numpy as np


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

            if not requested_custom_property and not requested_custom_function:
                # Filter by normal attributes
                objects = Filter.by_attr(objects, key, value, regex=True)
            elif requested_custom_property:
                # Filter by custom property
                objects = Filter.by_cp(objects, key, value, regex=True)
            elif requested_custom_function:
                # Build boundaries of interval
                conditions = Config(value)
                if conditions.has_param("min") and conditions.has_param("max"):
                    if any(conditions.has_param(key) for key in
                           ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"]):
                        raise RuntimeError("An inside/outside condition cannot mix the min/max vector syntax with "
                                           "the x_min/x_max/y_min/... syntax.")

                    bb_min = conditions.get_vector3d("min")
                    bb_max = conditions.get_vector3d("max")
                else:
                    if any(conditions.has_param(key) for key in ["min", "max"]):
                        raise RuntimeError("An inside/outside condition cannot mix the min/max syntax with "
                                           "the x_min/x_max/y_min/... syntax.")

                    # Set the interval +/- inf per default, so they will be ignored if they are not set
                    bb_min = mathutils.Vector((-np.inf, -np.inf, -np.inf))
                    bb_max = mathutils.Vector((np.inf, np.inf, np.inf))

                    # Set boundaries given by config
                    for axis_index in range(3):
                        axis_name = "xyz"[axis_index]
                        for direction in ["min", "max"]:
                            key_name = "{}_{}".format(axis_name, direction)
                            if key_name in value:
                                if direction == "min":
                                    bb_min[axis_index] = float(value[key_name])
                                else:
                                    bb_max[axis_index] = float(value[key_name])

                if key == "inside":
                    objects = Filter.by_attr_in_interval(objects, "location", bb_min, bb_max)
                elif key == "outside":
                    objects = Filter.by_attr_outside_interval(objects, "location", bb_min, bb_max)
                else:
                    raise Exception("No such custom function: " + str(key))

        return objects

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
        if not isinstance(conditions, list):
            conditions = [conditions]

        all_objects = convert_to_entities(bpy.context.scene.objects)
        filtered_objects = []
        # each single condition is treated as and condition
        for and_condition in conditions:
            new_filtered_objects = self.perform_and_condition_check(and_condition, all_objects)
            # Add objects to the total list, if they are not already present there
            filtered_objects.extend([obj for obj in new_filtered_objects if obj not in filtered_objects])

        random_samples = self.config.get_int("random_samples", 0)
        has_index = self.config.has_param("index")

        if has_index and random_samples:
            raise RuntimeError("Please, define only one of two: `index` or `random_samples`.")
        elif has_index:
            filtered_objects = [filtered_objects[self.config.get_int("index")]]
        elif random_samples:
            filtered_objects = sample(filtered_objects, k=min(random_samples, len(filtered_objects)))

        check_if_return_is_empty = self.config.get_bool("check_empty", False)
        if check_if_return_is_empty and not filtered_objects:
            raise Exception(f"There were no objects selected with the following "
                            f"condition: \n{self._get_conditions_as_string()}")

        # Map back to blender objects for now (TODO: Remove in the future)
        filtered_objects = [filtered_object.blender_obj for filtered_object in filtered_objects]

        return filtered_objects
