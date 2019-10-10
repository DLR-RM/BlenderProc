from src.main.Module import Module
import mathutils
import bpy
import numpy as np
import os


class LightPositioning(Module):
    """ Inserts lights as specified inside the configuration

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "lights", "A list of dicts, where each entry describes one light. See next table for which properties can be used."

    **Properties per light**:

    .. csv-table::
       :header: "Keyword", "Description"

       "type", "The strength of the light type. Has to be one of ['POINT', 'SUN', 'SPOT', 'AREA']"
       "location", "The position of the light, specified as a list of three values (xyz)."
       "rotation", "The rotation of the light, specified as a list of three euler angles."
       "energy", "The strength of the light."

    **Example**:

    The following example creates a simple point light:

    >>> "lights": [
    >>>   {
    >>>     "type": "POINT",
    >>>     "location": [5, -5, 5],
    >>>     "energy": 1000
    >>>   }
    >>> ]
    """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        for i, light in enumerate(self.config.get_list("lights")):
            if "type" not in light:
                raise Exception("Type of light not specified")

            # Create light data
            light_data = bpy.data.lights.new(name="light_" + str(i), type=light["type"])
            if "energy" in light:
                light_data.energy = light["energy"]

            # Link data with new object
            light_object = bpy.data.objects.new(name="light_" + str(i), object_data=light_data)
            bpy.context.collection.objects.link(light_object)

            if "location" in light:
                light_object.location = light["location"]

            if "rotation" in light:
                light_object.rotation_euler = light["rotation"]
