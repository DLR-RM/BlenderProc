from src.main.Module import Module


class Loader(Module):
    """
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "physics", "Determines the the physics property of all created objects. Set to ACTIVE if you want the objects to actively participate in the simulation and be influenced by e.q. gravity. Set to PASSIVE, if you want the object to be static and only act as an obstacle."
    """
    def __init__(self, config):
        Module.__init__(self, config)

    def _set_physics_property(self, objects):
        """ Sets the physics custom property of all given objects according to the configuration.

        :type objects: A list of objects which should retrieve the custom property.
        """
        for obj in objects:
            obj["physics"] = self.config.get_string("physics", "passive")
