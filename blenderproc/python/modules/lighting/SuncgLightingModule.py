from blenderproc.python.modules.main.Module import Module
from blenderproc.python.lighting.SuncgLighting import light_suncg_scene


class SuncgLightingModule(Module):
    """ Adds emission shader to lamps, windows and ceilings.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - lightbulb_emission_strength
          - The emission strength that should be used for light bulbs. Default: 15
          - float
        * - lampshade_emission_strength
          - The emission strength that should be used for lamp shades. Default: 7
          - float
        * - ceiling_emission_strength
          - The emission strength that should be used for the ceiling. Default: 1.5
          - float
    """
    def __init__(self, config):
        Module.__init__(self, config)
        
    def run(self):
        """
        Run this current module.
        """
        light_suncg_scene(self.config.get_float("lightbulb_emission_strength", 15), self.config.get_float("lampshade_emission_strength", 7), self.config.get_float("ceiling_emission_strength", 1.5))
