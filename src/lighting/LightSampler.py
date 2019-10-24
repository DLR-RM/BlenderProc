import mathutils
import bpy
import random

from src.lighting.LightModule import LightModule
from src.utility.Utility import Utility
from src.utility.BoundingBoxSampler import BoundingBoxSampler
from src.utility.SphereSampler import SphereSampler


class LightSampler(LightModule):
    """ Samples light source\'s settings and sets them.
    
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "A path to a file where values used for setting a ligt source(s) (like position, type, color, etc.) are written, onelight source per line."
    
    **Properties per sampling method**:

    .. csv-table::
       :header: "Keyword", "Description"

       "BoundingBoxSampling", "Uniform 3D sampling method that samples a random position inside a bounding box. See src/utility/BoundingBoxSampler.py for more info."
       "SphereSampling", "Samples a point in and inside a solid sphere. See src/utility/SphereSampler.py for more info."
    """

    def __init__(self, config):
        LightModule.__init__(self, config)

    def run(self):
        """ Sets light sources. """
        self.cross_source_settings = self._sample_settings(self.cross_source_settings)
        source_specs = self.config.get_list("lights", [])
        for i, source_spec in enumerate(source_specs):
            # Sample settings as specified in the config file
            sampled_settings = self._sample_settings(source_spec)

            # Add new light source based on the sampled settings
            self.light_source_collection.add_item(sampled_settings)

            # Write settings to file
            self._write_settings_to_file(sampled_settings, self.config.get_string("path", ""))
            
    def _sample_settings(self, source_spec):
        """ Samples the parameters according to user-defined sampling types in the configuration file.

        :param source_spec: Dict that contains settings defined in the config file.
        :return: Processed settings dict.
        """
        sampled_settings = {}
        for attribute_name, value in source_spec.items():
            # Check if settings value must be sampled
            if isinstance(value, dict):
                result = list(Utility.sample_based_on_config(value))
                sampled_settings.update({attribute_name: result})
            else:
                sampled_settings.update({attribute_name: value})

        return sampled_settings

    def _write_settings_to_file(self, sampled_settings, path):
        """ Writes light source settings used in a file.

        One light source is one line in the file, settings sorted alphabetically.

        :param sampled_settings: Dict with used settings where {key:value} pairs are {setting name: used setting value}.
        :param path: Path to output file specified in the configuration file.
        """
        line = ""
        # Sort merged source specific and cross source settings alphabetically
        settings_to_write = sorted(Utility.merge_dicts(sampled_settings, self.cross_source_settings).items(), key=lambda x: x[0])
        with open(Utility.resolve_path(path), 'a') as f:
            for item, value in settings_to_write:
                if not isinstance(value, list):
                    value = [value]
                line += " ".join(str(x) for x in value) + " "
            f.write('%s \n' % line)
