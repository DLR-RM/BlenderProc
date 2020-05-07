from src.lighting.LightModule import LightModule


class LightSampler(LightModule):
    """ Samples light source\'s settings and sets them.
    
    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "lights", "List of lights, which contain all the information to create new lights. See the LightModule for
                  "more information. Type: list. Default: []."
    """

    def __init__(self, config):
        LightModule.__init__(self, config)

    def run(self):
        """ Sets light sources. """
        source_specs = self.config.get_list("lights", [])
        for i, source_spec in enumerate(source_specs):
            # Add new light source based on the sampled settings
            self.light_source_collection.add_item(source_spec)

