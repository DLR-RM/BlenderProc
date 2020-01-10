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
        source_specs = self.config.get_list("lights", [])
        for i, source_spec in enumerate(source_specs):
            # Add new light source based on the sampled settings
            self.light_source_collection.add_item(source_spec)

