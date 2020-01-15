import bpy
import mathutils

class ObjectGetter:
    """ Returns a list of objects in accordance to a condition.

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

    "condition", "Dict with one entry of format {attribute_name: attribute_value}. Type: dict."
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

        for key, value in cond.items():

            for obj in bpy.context.scene.objects:

                if key in obj:

                    curr_type = type(obj[key])
                    if curr_type != type(value):
                        if 'Vector' in curr_type:
                            new_value = mathutils.Vector(value)
                        elif 'Euler' in curr_type:
                            new_value = mathutils.Euler(value)
                        elif 'Color' in curr_type:
                            new_value = mathutils.Color(value)
                        else:
                            raise Exception("Types are not matching: %s and %s !" % (type(obj[key]), type(value)))
                    else:
                        new_value = value

                    if obj[key] == new_value:
                        objects += [obj]

                if hasattr(obj, key):

                    curr_type = type(getattr(obj, key))
                    if curr_type != type(value):
                        if 'Vector' in curr_type:
                            new_value = mathutils.Vector(value)
                        elif 'Euler' in curr_type:
                            new_value = mathutils.Euler(value)
                        elif 'Color' in curr_type:
                            new_value = mathutils.Color(value)
                        else:
                            raise Exception("Types are not matching: %s and %s !" % (type(obj[key]), type(value)))
                    else:
                        new_value = value

                    if getattr(obj, key) == new_value:
                        objects += [obj]

            return objects
