import mathutils
import bpy
import numpy as np
import os

from src.main.Module import Module
from src.utility.ItemCollection import ItemCollection
from src.utility.Utility import Utility

class LightModule(Module):
    """ 
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "cross_source_settings", "A dict which can be used to specify properties across all light sources. See the next table for which properties can be set."

    **Properties per lights entry**:

    .. csv-table::
       :header: "Keyword", "Description"

       "location", "The position of the light source, specified as a list of three values."
       "rotation_euler", "The rotation of the light source, specified as a list of three euler angles."
       "color", "Light color, specified as a list of three values (each in [0, inf]) [R, G, B]"
       "distance", "Falloff distance of the light = point where light is half the original intensity. Specified as one value in [0, inf]."
       "energy", "Intensity of the emission of a light source, specified as a value in [-inf, inf]."
       "type", "The type of a light source. Has to be one of ['POINT', 'SUN', 'SPOT', 'AREA']"
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.cross_source_settings = self.config.get_raw_dict("cross_source_settings", {})
        self.light_source_collection = ItemCollection(self._add_light_source, self.cross_source_settings)

    def _add_light_source(self, config):
        """ Adds a new light source according to the given configuration.

        :param config: A configuration object which contains all parameters relevant for the new light source.
        """
        # Create light data, link it to the new object
        light_data = bpy.data.lights.new(name="light", type="POINT")
        light_obj = bpy.data.objects.new(name="light", object_data=light_data)
        bpy.context.collection.objects.link(light_obj)

        light_data.type = config.get_string("type", 'POINT')
        light_obj.location = config.get_list("location", [0, 0, 0])
        light_obj.rotation_euler = config.get_list("rotation", [0, 0, 0])
        light_data.energy = config.get_float("energy", 10)
        light_data.color = config.get_list("color", [1, 1, 1])
        light_data.distance = config.get_float("distance", 0)

