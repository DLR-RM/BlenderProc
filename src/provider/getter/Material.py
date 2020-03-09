import bpy
import mathutils
import re

from src.main.Provider import Provider

class Material(Provider):


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
        new_materials = []
        # through every object
        for material in bpy.data.materials:
            if material in new_materials:
                continue

            select_object = True
            for key, value in and_condition.items():
                if hasattr(material, key):
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
                            raise Exception("Types are not matching: %s and %s !"
                                            % (type(getattr(material, key)), type(value)))
                    # or check for equality
                    if not ((isinstance(getattr(material, key), str) and re.fullmatch(value, getattr(material, key)) is not None)
                            or getattr(material, key) == new_value):
                        select_object = False
                        break
            if select_object:
                new_materials.append(material)
        print("New materials: {}".format(new_materials))
        return new_materials

    def run(self):
        """
        :return: List of materials that met the conditional requirement.
        """
        conditions = self.config.get_raw_dict('conditions')
        print(conditions)
        return self.perform_and_condition_check(conditions, [])
