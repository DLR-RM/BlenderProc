from src.main.Module import Module
import mathutils
import bpy
import numpy as np
import os


class LightPositioning(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        for i, light in enumerate(self.config.get_list("lights")):
            if "type" not in light:
                raise Exception("Type of light not specified")

            light_data = bpy.data.lights.new(name="light_" + str(i), type=light["type"])
            if "energy" in light:
                light_data.energy = light["energy"]

            light_object = bpy.data.objects.new(name="light_" + str(i), object_data=light_data)

            bpy.context.collection.objects.link(light_object)

            if "location" in light:
                light_object.location = light["location"]

            if "rotation" in light:
                light_object.rotation_euler = light["rotation"]
