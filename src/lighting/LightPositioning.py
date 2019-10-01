from src.main.Module import Module
import mathutils
import bpy
import numpy as np
import os


class LightPositioning(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Inserts lights as specified inside the configuration:

            e.q.:
            "lights": [
              {
                "type": "POINT",
                "location": [5, -5, 5],
                "energy": 1000
              }
            ]
        """
        for i, light in enumerate(self.config.get_list("lights")):
            if "type" not in light:
                raise Exception("Type of light not specified")

            # Create light data
            light_data = bpy.data.lights.new(name="light_" + str(i), type=light["type"])
            if "energy" in light:
                light_data.energy = light["energy"]
            if "shape" in light:
                light_data.shape = light["shape"]
            if "size" in light:
                light_data.size = light["size"]

            # Link data with new object
            light_object = bpy.data.objects.new(name="light_" + str(i), object_data=light_data)
            bpy.context.collection.objects.link(light_object)

            if "location" in light:
                light_object.location = light["location"]
            
            if "rotation" in light:
                light_object.rotation_euler = light["rotation"]
