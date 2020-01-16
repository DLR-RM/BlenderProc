import bpy
import mathutils
import re

from src.main.Provider import Provider

class Object(Provider):
    """ Returns a list of objects in accordance to a condition.
    Specify a desired condition in the format {attribute_name: attribute_value}, note that attribute_value for a custom
    property can be a string/int/bool/float, while only attribute_value for valid attributes of objects can be a list
    (mathutils.Vector, mathurils.Color and mathutils.Euler are covered by 'list' type).

    NOTE: any given attribute_value of the type string will be treated as a REGULAR EXPRESSION.

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
        cond = self.config.get_raw_dict('condition')
        if len(cond) > 1:
            raise Exception('ObjectGetter supports only one condition (for now)!')

        objects = []
        # through every key-value/name-value pair in condition
        for key, value in cond.items():
            # through every object
            for obj in bpy.context.scene.objects:
                # check if a custom property with this name exists
                if key in obj:
                    # check if the type of the value of such custom property matches desired
                    if isinstance(obj[key], type(value)):
                        # if is a string and if search is not returning None which means that we have a match
                        if isinstance(obj[key], str) and re.search(value, obj[key]) is not None:
                            objects.append(obj)
                        # check for equality
                        elif obj[key] == value:
                            objects.append(obj)
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
                    if isinstance(getattr(obj, key), str) and re.search(value, getattr(obj, key)) is not None:
                        objects.append(obj)
                        # check for equality
                    # finally check for equality
                    elif getattr(obj, key) == new_value:
                        objects.append(obj)

            return objects
