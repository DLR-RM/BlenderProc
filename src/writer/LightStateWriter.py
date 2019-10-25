from src.utility.ItemWriter import ItemWriter
import bpy
import os

from src.writer.StateWriter import StateWriter


class LightStateWriter(StateWriter):
    """ Writes the state of all lights for each frame to a file.

    **Attributes per object**:

    .. csv-table::
     :header: "Keyword", "Description"

     "energy", "The energy of the light"
    """

    def __init__(self, config):
        StateWriter.__init__(self, config)
        self.light_writer = ItemWriter(self._get_attribute)

    def run(self):
        # Collection all lights
        lights = []
        for object in bpy.context.scene.objects:
            if object.type == 'LIGHT':
                lights.append(object)

        self.write_attributes_to_file(self.light_writer, lights, "light_states_", "light_states", ["id", "location", "rotation_euler", "energy"])

    def _get_attribute(self, light, attribute_name):
        """ Returns the value of the requested attribute for the given light.

        :param light: The light.
        :param attribute_name: The attribute name.
        :return: The attribute value.
        """
        if attribute_name == "energy":
            return light.data.energy
        else:
            return super()._get_attribute(light, attribute_name)
