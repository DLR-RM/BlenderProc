from src.main.Module import Module

class Loader(Module):
    """
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       "add_properties", "Custom properties to set for loaded objects. Use 'cp_' prefix for keys. Type: dict."
    """
    def __init__(self, config):
        Module.__init__(self, config)

    def _set_properties(self, objects):
        """ Sets all custom properties of all given objects according to the configuration.

        :parameter objects: A list of objects which should receive the custom properties
        """

        properties = self.config.get_raw_dict("add_properties", {})

        for obj in objects:
            for key, value in properties.items():
                if key.startswith("cp_"):
                    key = key[3:]
                    obj[key] = value
                else:
                    raise RuntimeError("Loader modules support setting only custom properties. Use 'cp_' prefix for keys. "
                                       "Use manipulators.Entity for setting object's attribute values.")
