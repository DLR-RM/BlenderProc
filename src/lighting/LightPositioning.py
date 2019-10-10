from src.main.Module import Module
import mathutils
import bpy
import numpy as np
import os
import random

from src.utility.Utility import Utility

class LightPositioning(Module):
    """ Inserts light as specified in the config.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "lights", "A list of dicts, where each entry describes one light. See next table for which properties can be used."
       "path", "Optionally, a path to a file which specifies one light source position, type, etc. per line. The lines has to be formatted as specified in 'file_format'."
       "file_format", "file_format", "A string which specifies how each line of the given file is formatted. The string should contain the keywords of the corresponding properties separated by a space. See next table for allowed properties."
       "default_source_param", "A dict which can be used to specify properties across all light sources. See the next table for which properties can be set."

    **Properties per lights entry**:

    .. csv-table::
       :header: "Keyword", "Description"

       "location", "The position of the light source, specified as a list of three values."
       "rotation_euler", "The rotation of the light source, specified as a list of three euler angles."
       "color", "Light color, specified as a list of three values (each in [0, inf]) [R, G, B]"
       "distance", "Falloff distance of the light = point where light is half the original intensity. Specified as one value in [0, inf]."
       "energy", "Intensity of the emission of a light source, specified as a value in [=inf, inf]."
       "type", "The type of a light source. Has to be one of ['POINT', 'SUN', 'SPOT', 'AREA']"
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.file_format = self.config.get_string("file_format", "").split()
        # Number of values per available attribute option.
        self.light_source_attribute_length = {
            "location": 3,
            "rotation_euler": 3,
            "color": 3,
            "distance": 1,
            "energy": 1,
            "type": 1
        }
        # Settings of a default llight source, can be partially rewrited by default_source_param section of the configuration file
        self.default_source_specs = {
            "location": [5, 5, 5],
            "color": [1.0, 1.0, 1.0],
            "distance": 0,
            "type": 'POINT',
            "energy": 0
        }
        # Length of the entry line yet to be extracted from a separate file based on the file_format section of the configuration file
        self.file_format_length = sum([self._length_of_attribute(attribute) for attribute in self.file_format])

    def run(self):
        """ Sets light sources from a configuration.
        
        Position, type and intensity of the light source\'s emission can be specified either directly in the the config file or in an external file.
        """		
        # Add a light source as specified in the config file
        source_specs = self.config.get_list("lights", [])
        for i, source_spec in enumerate(source_specs):
            # Create light data, link it to the new object
            light_data = bpy.data.lights.new(name="light_" + str(i), type=self.default_source_specs["type"])
            light_obj = bpy.data.objects.new(name="light_" + str(i), object_data=light_data)
            bpy.context.collection.objects.link(light_obj)
            # Set default light source
            self._init_default_light_source(light_data, light_obj)
            # Configure default light source
            self._set_light_source_from_config(light_data, light_obj, source_spec)
        path = self.config.get_string("path", "")
        # Add a light source as specified in a separate file
        for source_spec in self._collect_source_specs_from_file(path):
            # Create light data, link it to the new object
            light_data = bpy.data.lights.new(name="light_" + str(i), type=self.default_source_specs["type"])
            light_obj = bpy.data.objects.new(name="light)" + str(i), object_data=light_data)
            bpy.context.collection.objects.link(light_obj)
            # Set default light source
            self._init_default_light_source(light_data, light_obj)
            # Configure default light source
            self._set_light_source_from_file(light_data, light_obj, source_spec)

    def _collect_source_specs_from_file(self, path):
        """ Reads in all lines of the given file and returns values as a list of lists of arguments.

        Also checks if the lines read are matching the stated file format.

        :param path: The path to the file
        :return: A list of lists of arguments
        """
        source_specs = [];
        if path != "":
            with open(Utility.resolve_path(path)) as f:
                lines = f.readlines()
                lines = [line for line in lines if len(line.strip()) > 3]
                for line in lines:
                    source_specs_entry = line.strip().split()
                    # Check for file format matching
                    if len(source_specs_entry) != self.file_format_length:
                        raise Exception("A line in the given light source specifications file does not match the configured file format:\n" + line.strip() + " (Number of values: " + str(len(source_specs_entry)) + ")\n" + str(self.file_format) + " (Number of values: " + str(self.file_format_length) + ")")
                    # Check it type of the light source was specified
                    if "type" in self.file_format:
                        idx = sum([self._length_of_attribute(attribute) for attribute in self.file_format[0:self.file_format.index('type')]])
                        source_specs.append([float(x) if source_specs_entry.index(x) is not idx else x for x in source_specs_entry])
                    else:
                        source_specs.append([float(x) for x in source_specs_entry])
        
        return source_specs

    def _init_default_light_source(self, light_data, light_obj):
        """ Sets a light source using the default parameters.
        
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purpose of general properties determining.	
        """
        # Overwrite default settings with user\'s settings specified in default_source_param section of the configuration file
        config = Utility.merge_dicts(self.config.get_raw_dict("default_source_param", {}), self.default_source_specs)
        self._set_light_source_from_config(light_data, light_obj, config)

    def _set_light_source_from_file(self, light_data, light_obj, source_specs):
        """ Sets the light source\'s parameters using the specs extracted from the given file.
        	
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purpose of general properties determining.
        :param source_specs: Arguments extracted from the external file.
        """
        # Go throught all configured attrubutes, set current one using N next argument
        for attribute in self.file_format:
            self._set_attribute(light_data, light_obj, attribute, source_specs[:self._length_of_attribute(attribute)])
            source_specs = source_specs[self._length_of_attribute(attribute):]

    def _set_light_source_from_config(self, light_data, light_obj, source_specs):
        """ Sets the light source\'s parameters using the given config dict.
        
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purpose of general properties determining.
        :param source_specs: Dict where key - attribute name, value - value of this attribute.
        """
        # Go through all key-value pairs of the dict, set the corresponding attributes
        for attribute_name, value in source_specs.items():
            self._set_attribute(light_data, light_obj, attribute_name, value)

    def _length_of_attribute(self, attribute):
        """ Returns how many arguments the given attribute expects.

        :param attribute: The name of the attribute
        :return: The expected number of arguments
		"""
        # If not set, return 1
        if attribute in self.light_source_attribute_length:
            return self.light_source_attribute_length[attribute]
        else:
            return 1

    def _set_attribute(self, light_data, light_obj, attribute_name, value):
        """ Sets the value of a given attribute.
        
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for porposes of general properties determining.	
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
        elif attribute_name == 'energy':
            # Intensity of the emission of a light source
            light_data.energy == value[0]
        elif attribute_name == 'color':
            # Color of a light
            light_data.color = value
        elif attribute_name == 'distance':
            # Falloff distance
            light_data.distance = value[0]
        elif attribute_name == "_":
            # Skip
            pass
        else:
            raise Exception("Unknown attribute: " + attribute_name)

