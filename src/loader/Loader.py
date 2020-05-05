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
        self.nyu_label_index_map = {'toilet': 33, 'whiteboard': 30, 'wall': 1, 
        'otherstructure': 38, 'night_stand': 32, 'otherprop': 40, 'books': 23, 
        'mirror': 19, 'table': 7, 'chair': 5, 'otherfurniture': 39, 'floor': 2, 
        'lamp': 35, 'window': 9, 'refridgerator': 24, 'curtain': 16, 
        'blinds': 13, 'dresser': 17, 'picture': 11, 'ceiling': 22, 
        'door': 8, 'shower_curtain': 28, 'void': 0, 'cabinet': 3, 
        'sink': 34, 'desk': 14, 'bookshelf': 10, 'towel': 27, 'box': 29, 
        'television': 25, 'floor_mat': 20, 'shelves': 15, 'sofa': 6, 
        'counter': 12, 'bed': 4, 'person': 31, 'paper': 26, 
        'bag': 37, 'bathtub': 36, 'pillow': 18, 'clothes': 21}

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
