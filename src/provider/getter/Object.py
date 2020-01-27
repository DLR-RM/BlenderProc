import bpy
import mathutils
import re

from src.main.Provider import Provider

class Object(Provider):
    """ Returns a list of objects in accordance to a condition.
    Specify a desired condition in the format {attribute_name: attribute_value}, note that attribute_value for a custom
    property can be a string/int/bool/float, while only attribute_value for valid attributes of objects can be a bool or a
    list (mathutils.Vector, mathurils.Color and mathutils.Euler are covered by 'list' type).

    NOTE: any given attribute_value of the type string will be treated as a REGULAR EXPRESSION.

    An example:
        "name_of_selector": {
            "provider": "getter.Object"
            "conditions": {
                "name": "Suzanne"   # this checks if the name of the object is equal to Suzanne (treated as a regular expr.)
            }
        }
    Another more complex example:
    Here all objects which are either named Suzanne or (the name starts with Cube and belong to the category "is_cube")
        "name_of_selector": {
            "provider": "getter.Object"
            "conditions": [{
                "name": "Suzanne"   # this checks if the name of the object is equal to Suzanne (treated as a regular expr.)
            },{
                "name": "Cube*",   # this checks if the name of the object starts with Cube (treated as a regular expr.)
                "category": "is_cube" # both have to be true
            }
            ]
        }

    This means: conditions, which are in one {...} are connected with AND, conditions which are in the
    list are connected with or

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

    "condition", "Dict with one entry of format {attribute_name: attribute_value}. Type: dict."
    "condition/attribute_name", "Name of any valid object's attribute or custom property. Type: string."
    "condition/attribute_value", "Any value to set. Types: string, int, bool or float, list/Vector/Euler/Color."
    """
    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: List of objects that met the conditional requirement.
        """
        conditions = self.config.get_raw_dict('conditions')

        def perform_and_condition_check(and_condition, objects):
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
                    # check if a custom property with this name exists
                    if key in obj:
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
                    # check if an attribute with this name exists
                    if hasattr(obj, key):
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
                    else:
                        select_object = False
                        break
                if select_object:
                    new_objects.append(obj)
            return new_objects

        # the list of conditions is treated as or condition
        if isinstance(conditions, list):
            objects = []
            # each single condition is treated as and condition
            for and_condition in conditions:
                objects.extend(perform_and_condition_check(and_condition, objects))
        else:
            # only one condition was given, treat it as and condition
            objects = perform_and_condition_check(conditions, [])
        return objects
