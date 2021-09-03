import bpy

from blenderproc.python.modules.utility.ItemWriter import ItemWriter
from blenderproc.python.modules.writer.WriterInterface import WriterInterface
from blenderproc.python.writer.WriterUtility import WriterUtility


class LightStateWriter(WriterInterface):
    """ Writes the state of all lights for each frame to a file.
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        self.light_writer = ItemWriter(WriterUtility.get_light_attribute)

    def run(self):
        """ Collection all lights and writes them to a numpy file if no hdf5 file was available"""
        lights = []
        for object in bpy.context.scene.objects:
            if object.type == 'LIGHT':
                lights.append(object)

        self.write_attributes_to_file(self.light_writer, lights, "light_states_", "light_states",
                                      ["location", "rotation_euler", "energy"])


