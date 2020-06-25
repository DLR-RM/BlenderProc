import bpy

from src.utility.ItemWriter import ItemWriter
from src.writer.Writer import Writer


class LightStateWriter(Writer):
    """ Writes the state of all lights for each frame to a file.

    **Attributes per object**:

    .. csv-table::
     :header: "Keyword", "Description"


    """

    def __init__(self, config):
        Writer.__init__(self, config)
        self.light_writer = ItemWriter(self._get_attribute)

    def run(self):
        """ Collection all lights and writes them to a numpy file if no hdf5 file was available"""
        lights = []
        for object in bpy.context.scene.objects:
            if object.type == 'LIGHT':
                lights.append(object)

        self.write_attributes_to_file(self.light_writer, lights, "light_states_", "light_states",
                                      ["id", "location", "rotation_euler", "energy"])

    def _get_attribute(self, light, attribute_name):
        """ Returns the value of the requested attribute for the given light.

        :param light: The light. Type: blender scene object of type light.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """
        if attribute_name == "energy":
            return light.data.energy
        else:
            return super()._get_attribute(light, attribute_name)
