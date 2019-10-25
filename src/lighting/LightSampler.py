import mathutils
import bpy
import random

from src.lighting.LightModule import LightModule
from src.utility.Utility import Utility


class LightSampler(LightModule):
    """ Samples light source\'s settings and sets them.
    
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "A path to a file where values used for setting a ligt source(s) (like position, type, color, etc.) are written, onelight source per line."
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

