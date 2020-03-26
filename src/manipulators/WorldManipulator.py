import bpy
from src.main.Module import Module


class WorldManipulator(Module):
    """ Allows basic manipulation of the blender world. Specify any desired {key: value} pairs.
    Each pair is treated like a {attribute_name:attribute_value} where attr_name is a custom property or a name of a
     custom property to create, while the attr_value is its new value.


    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "custom_property_name": "Value that custom_property should be set to."
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        for key in self.config.data.keys():
            bpy.context.scene.world[key] = self.config.get_raw_value(key)
