from src.main.Module import Module
import mathutils
import bpy
import numpy as np
import os
import random

from src.utility.Utility import Utility

class LightPositioning(Module):

    def __init__(self, config):
        Module.__init__(self, config)
        self.file_format = self.config.get_string("file_format", "").split()
        self.light_source_attribute_length = {
            "location": 3,
            "rotation_euler": 3,
            "random_location": 6,
            "color": 3,
            "distance": 1,
            "energy": 1,
            "type": 1
        }
        self.default_source_specs = {
            "location": [5, 5, 5],
            "color": [0, 0, 0],
            "distance": 0,
            "type": 'POINT',
            "energy": 0
        }
        self.file_format_length = sum([self._length_of_attribute(attribute) for attribute in self.file_format])

    def run(self):
        """ Sets light sources from a configuration.
        
        Position, type and intensity of the light source\'s emission can be specified either directly in the the config file or in an external file.
        """		
        # Add a light source as specified in the config file
        source_specs = self.config.get_list("lights", [])
        for i, source_spec in enumerate(source_specs):
            light_data = bpy.data.lights.new(name="light_" + str(i), type=self.default_source_specs["type"])
            light_obj = bpy.data.objects.new(name="light_" + str(i), object_data=light_data)
            bpy.context.collection.objects.link(light_obj)
            self._init_default_light_source(light_data, light_obj)
            self._set_light_source_from_config(light_data, light_obj, source_spec)
        path = self.config.get_string("path", "")
        i = 0
        for source_spec in self._collect_source_specs_from_file(path):	
            light_data = bpy.data.lights.new(name="light_" + str(i), type=self.default_source_specs["type"])
            light_obj = bpy.data.objects.new(name="light)" + str(i), object_data=light_data)
            bpy.context.collection.objects.link(light_obj)
            self._init_default_light_source(light_data, light_obj)
            self._set_light_source_from_file(light_data, light_obj, source_spec)
            i = i+1

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
        config = Utility.merge_dicts(self.config.get_raw_dict("default_source_param", {}), self.default_source_specs)
        self._set_light_source_from_config(light_data, light_obj, config)

    def _collect_light_specs_from_config(self):
        """ Reads the settings given in main config file and returns them as a list of dicts.
        	
        Checks for settings absence and if needed set some default values for them.
            
        :return: A list of dicts of arguments.
        """
        pass

    def _set_light_source_from_file(self, light_data, light_obj, source_specs):
        """ Sets the light source\'s parameters using the specs extracted from the given file.
        	
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purpose of general properties determining.
        :param source_specs: Arguments extracted from the external file.
        """
        # set params thru _set_attributes
        for attribute in self.file_format:
            self._set_attribute(light_data, light_obj, attribute, source_specs[:self._length_of_attribute(attribute)])
            source_specs = source_specs[self._length_of_attribute(attribute):]

    def _set_light_source_from_config(self, light_data, light_obj, source_specs):
        """ Sets the light source\'s parameters using the given config dict.
        les/basic/output[B> firefox rgb_0001.png
olef_dm@rmc-lx0211:~/work/Blender-Pipeline/examp
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purpose of general properties determining.
        :param source_specs: Dict where key - attribute name, value - value of this attribute.
        """
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
        # set values for light_data and light_obj
        if not isinstance(value, list):
            value = [value]
        
        if attribute_name == 'type':
            light_data.type = value[0]
        elif attribute_name == 'location':
            light_obj.location = value
        elif attribute_name == 'rotation_euler':
            light_obj.rotation_euler == value
        elif attribute_name == 'random_location':
            light_obj.location = [random.uniform(value[0], value[1]), random.uniform(value[2], value[3]), random.uniform(value[4], value[5])]
        elif attribute_name == 'energy':
            light_data.energy == value[0]
        elif attribute_name == 'color':
            light_data.color = value
        elif attribute_name == 'distance':
            light_data.distance = value[0]
        elif attribute_name == "_":
            pass
        else:
            raise Exception("Unknown attribute: " + attribute_name)

