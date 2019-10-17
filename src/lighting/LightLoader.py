import mathutils
import bpy

from src.lighting.LightModule import LightModule
from src.utility.Utility import Utility


class LightLoader(LightModule):
    """ Loads light source\'s settings and sets them.

    Settings can be defined in the config file in the corresponding section or in the external file.
    
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
    
       "lights", "A list of dicts, where each entry describes one light. See next table for which properties can be used."
       "path", "Optionally, a path to a file which specifies one light source position, type, etc. per line. The lines has to be formatted as specified in 'file_format'."
       "file_format", "file_format", "A string which specifies how each line of the given file is formatted. The string should contain the keywords of the corresponding properties separated by a space. See LightModule for allowed properties."
    """

    def __init__(self, config):
        LightModule.__init__(self, config)
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
        # Length of the entry line yet to be extracted from a separate file based on the file_format section of the configuration file
        self.file_format_length = sum([self._length_of_attribute(attribute, self.light_source_attribute_length) for attribute in self.file_format])

    def run(self):
        """ Sets light sources from config and loads them from file.
        
        """		
        # Add a light source as specified in the config file
        source_specs = self.config.get_list("lights", [])
        for i, source_spec in enumerate(source_specs):
            # Create light data, link it to the new object
            light_data = bpy.data.lights.new(name="light_" + str(i), type=self.default_source_settings["type"])
            light_obj = bpy.data.objects.new(name="light_" + str(i), object_data=light_data)
            # Set default light source
            self._init_default_light_source(light_data, light_obj)
            # Configure default light source
            self._set_light_source_from_config(light_data, light_obj, source_spec)
            bpy.context.collection.objects.link(light_obj)

        path = self.config.get_string("path", "")
        # Add a light source as specified in a separate file
        for source_spec in self._collect_source_specs_from_file(path):
            # Create light data, link it to the new object
            light_data = bpy.data.lights.new(name="light_" + str(i), type=self.default_source_settings["type"])
            light_obj = bpy.data.objects.new(name="light_" + str(i), object_data=light_data)
            # Set default light source
            self._init_default_light_source(light_data, light_obj)
            # Configure default light source
            self._set_light_source_from_config(light_data, light_obj, source_spec)
            bpy.context.collection.objects.link(light_obj)

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
                        idx = sum([self._length_of_attribute(attribute, self.light_source_attribute_length) for attribute in self.file_format[0:self.file_format.index('type')]])
                        source_specs.append([float(x) if source_specs_entry.index(x) is not idx else x for x in source_specs_entry])
                    else:
                        source_specs.append([float(x) for x in source_specs_entry])
        return source_specs

    def _set_light_source_from_file(self, light_data, light_obj, source_specs):
        """ Sets the light source\'s parameters using the specs extracted from the given file.
        	
        :param light_data: Light source containing light-specific attributes.
        :param light_obj: The object linked to the light source for purpose of general properties determining.
        :param source_specs: Arguments extracted from the external file.
        """
        # Go throught all configured attrubutes, set current one using N next argument
        for attribute in self.file_format:
            self._set_attribute(light_data, light_obj, attribute, source_specs[:self._length_of_attribute(attribute, self.light_source_attribute_length)])
            source_specs = source_specs[self._length_of_attribute(attribute, self.light_source_attribute_length):]

