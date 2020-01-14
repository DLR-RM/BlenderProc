import bpy


class ObjectStringGetter:
    """ Returns a list of objects in accordance to a condition.

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

    "condition", "Dict with one entry of format {attribute_name: attribute_value} (both must be a string). Type: dict."
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
            if isinstance(value, str):
                for obj in bpy.context.scene.objects:
                    if key in obj:
                        if obj[key] == value:
                            objects += [obj]
                    if hasattr(obj, key):
                        if getattr(obj, key) == value:
                            objects += [obj]
            else:
                raise Exception('ObjectStringGetter supports only string-based values in condition!')

            return objects
