import bpy
import mathutils
import re

from src.main.Provider import Provider
from src.utility.Config import Config


class Entity(Provider):
    """ Returns a list of objects in accordance to a condition.
    Specify a desired condition in the format {attribute_name: attribute_value}, note that attribute_value for a custom
    property can be a string/int/bool/float, while only attribute_value for valid attributes of objects can be a bool or a
    list (mathutils.Vector, mathurils.Color and mathutils.Euler are covered by 'list' type).

    NOTE: any given attribute_value of the type string will be treated as a REGULAR EXPRESSION.

    An example:
        "name_of_selector": {
            "provider": "getter.Entity"
            "conditions": {
                "name": "Suzanne"   # this checks if the name of the object is equal to Suzanne (treated as a regular expr.)
            }
        }
    Another more complex example:
    Here all objects which are either named Suzanne or (the name starts with Cube and belong to the category "is_cube")
        "name_of_selector": {
            "provider": "getter.Entity",
            "index": 0,             # only returns the first match
            "conditions": [{
                "name": "Suzanne",  # this checks if the name of the object is equal to Suzanne (treated as a regular expr.)
                "type": "MESH"      # this will make sure that the object is a mesh
            },{
                "name": "Cube.*",   # this checks if the name of the object starts with Cube (treated as a regular expr.)
                "category": "is_cube" # both have to be true
            },{
                "inside": {         # this checks if the object is inside the bounding box defined by min and max points
                    "min": "[-5, -5, -5]", # or use "outside" for checking whether the obj is outside of b box
                    "max": "[5, 5, 5]"
                },
            },{
                "inside": {         # alternative syntax for inside/outside, cannot be mixed with min/max vector syntax
                    "z_min": -1,    # any object with a z position greater than -1
                    # supported keys: [xyz]_{min,max}
                    # missing arguments extend the bounding box to infinity in that direction
                },
            ]
        }

    This means: conditions, which are in one {...} are connected with AND, conditions which are in the
    list are connected with or.

    In the event that a custom property has the same name as an attribute of the object, the attribute is always
    evaluated first. In order to change let the key start with "cp_". For example there is a custom property with the
    key "type", so checking "type": "MESH" will lead to a problem, because the attribute will be checked.
    To avoid this change the key: "type" to "cp_type".

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

    "condition", "Dict with one entry of format {attribute_name: attribute_value}. Type: dict."
    "condition/attribute_name", "Name of any valid object's attribute or custom property. Type: string."
    "condition/attribute_value", "Any value to set. Types: string, int, bool or float, list/Vector/Euler/Color."
    "index", "If set, after the conditions are applied only the entity with the specified index is returned. Type: int"
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def perform_and_condition_check(self, and_condition, objects):
        """
        Checks for all objects in the scene if all given conditions are true, collects them in the return list
        See class description on how to set up AND and OR connections.
        :param and_condition: Given dictionary with conditions
        :param objects: list of objects, which already have been used
        :return: list of objects, which full fill the conditions
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
                if key.startswith('cp_'):
                    requested_custom_property = True
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
                elif key in obj:
                    # check if the type of the value of such custom property matches desired
                    if isinstance(obj[key], type(value)) or (isinstance(obj[key], int) and isinstance(value, bool)):
                        # if is a string and if the whole string matches the given pattern
                        if not ((isinstance(obj[key], str) and re.fullmatch(value, obj[key]) is not None) or
                                obj[key] == value):
                            select_object = False
                            break
                    # raise an exception if not
                    else:
                        raise Exception("Types are not matching: %s and %s !"
                                        % (type(obj[key]), type(value)))
                elif key == "inside" or key == "outside":
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

    def run(self):
        """
        :return: List of objects that met the conditional requirement.
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

        if self.config.has_param("index"):
            objects = [objects[self.config.get_int("index")]]

        return objects
