from blenderproc.python.modules.lighting.LightInterface import LightInterface


class LightSampler(LightInterface):
    """ Samples light source\'s settings and sets them.
    
    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - lights
          - List of lights, which contain all the information to create new lights. See the LightInterface for 
            more information. Default: [].
          - list
    """

    def __init__(self, config):
        LightInterface.__init__(self, config)

    def run(self):
        """ Sets light sources. """
        source_specs = self.config.get_list("lights", [])
        for i, source_spec in enumerate(source_specs):
            # Add new light source based on the sampled settings
            self.light_source_collection.add_item(source_spec)
