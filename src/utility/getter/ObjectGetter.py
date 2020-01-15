import bpy
import mathutils


class ObjectGetter:
    """ Returns a list of objects in accordance to a condition.
    Specify a desired condition in the format {attribute_name: attribute_value}, note that attribute_value for a custom
    property can be a string/int/bool/float, while only attribute_value for valid attributes of objects can be a list
    (mathutils.Vector, mathurils.Color and mathutils.Euler are covered by 'list' type).

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

    "condition", "Dict with one entry of format {attribute_name: attribute_value}. Type: dict."
    "condition/attribute_name", "Name of any valid object's attribute or custom property. Type: string."
    "condition/attribute_value", "Any value to set. Types: string, int, bool or float, list/Vector/Euler/Color."
    """

    @staticmethod
    def get(config):
        """
        :param config: Config objects with user-defined properties.
        :return: List of objects that met the conditional requirement.
        """
        cond = config.get_raw_dict('condition')
        if len(cond) > 1:
            raise Exception('ObjectGetter supports only one condition!')

        objects = []
        # through every key-value/name-value pair in condition
        for key, value in cond.items():
            # through every object
            for obj in bpy.context.scene.objects:
                # check if a custom property with this name exists
                if key in obj:
                    # check if the type of the value of such custom property matches desired
                    if isinstance(obj[key], type(value)):
                        # check for equality
                        if obj[key] == value:
                            objects += [obj]
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
                    # finally check for equality
                    if getattr(obj, key) == new_value:
                        objects += [obj]

            return objects
