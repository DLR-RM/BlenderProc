import mathutils
import bpy
import numpy as np
import os

from src.main.Module import Module
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
        # Default settings used by Blender, used for initializing a default light source.
        self.fallback_settings = {
            "location": [0, 0, 0],
            "color": [1, 1, 1],
            "energy": 10,
            "type": 'POINT',
            "distance": 0
        }
        self.cross_source_settings = self.config.get_raw_dict("cross_source_settings", {})

    def _init_default_light_source(self, light_data, light_obj):
        """ Sets a light source using the default parameters.
        
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purpose of general properties determining.	
        """
        # Overwrite default settings with user\'s settings specified in default_source_param section of the configuration file
        config = Utility.merge_dicts(self.cross_source_settings, self.fallback_settings)
        self._set_light_source_from_config(light_data, light_obj, config)

    def _set_light_source_from_config(self, light_data, light_obj, source_specs):
        """ Sets the light source\'s parameters using the given config dict.
        
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purpose of general properties determining.
        :param source_specs: Dict where key - attribute name, value - value of this attribute.
        """
        # Go through all key-value pairs of the dict, set the corresponding attributes
        for attribute_name, value in source_specs.items():
            self._set_attribute(light_data, light_obj, attribute_name, value)

    def _set_attribute(self, light_data, light_obj, attribute_name, value):
        """ Sets the value of a given attribute.
        
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purposes of general properties determining.	
        :attribute_name: The name of an attribute to be changed.
        :param value: The value to set.
        """
        # Check if value is a list, if not - make it a list
        if not isinstance(value, list):
            value = [value]

        if attribute_name == 'type':
            # Type of a light source
            light_data.type = value[0]
        elif attribute_name == 'location':
            # X, Y ,Z coordinates of a light source
            light_obj.location = value
        elif attribute_name == 'rotation_euler':
            # Rotation if the form of euler angles
            light_obj.rotation_euler == value
        elif attribute_name == 'color':
            # Color of a light
            light_data.color = value
        elif attribute_name == 'energy':
            light_data.energy = value[0]
        elif attribute_name == 'distance':
            # Falloff distance
            light_data.distance = value[0]
        elif attribute_name == "_":
            # Skip
            pass
        else:
            raise Exception("Unknown attribute: " + attribute_name)

    def _length_of_attribute(self, attribute, length_dict):
        """ Returns how many arguments the given attribute expects.

        :param attribute: The name of the attribute
        :param length_dict: Dict where {key:value} pairs are {name of the attrubute:expected length of an attribute} pairs.
        :return: The expected number of arguments
		"""
        # If not set, return 0
        if attribute in length_dict:
            return length_dict[attribute]
        else:
            return 0

