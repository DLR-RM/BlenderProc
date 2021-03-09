from src.utility.BlenderUtility import get_all_mesh_objects
from src.utility.ItemWriter import ItemWriter
from src.writer.WriterInterface import WriterInterface
from src.utility.WriterUtility import WriterUtility


class ObjectStateWriter(WriterInterface):
    """ Writes the state of all objects for each frame to a numpy file if no hfd5 file is available. """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        self.object_writer = ItemWriter(WriterUtility.get_common_attribute)

    def run(self):
        """ Collect all mesh objects and writes their id, name and pose."""
        objects = []
        for object in get_all_mesh_objects():
            objects.append(object)

        self.write_attributes_to_file(self.object_writer, objects, "object_states_", "object_states",
                                      ["name", "location", "rotation_euler", "matrix_world"])

