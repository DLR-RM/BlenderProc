from src.utility.BlenderUtility import get_all_mesh_objects
from src.utility.ItemWriter import ItemWriter
from src.writer.WriterInterface import WriterInterface


class ObjectStateWriter(WriterInterface):
    """ Writes the state of all objects for each frame to a numpy file if no hfd5 file is available. """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        self.object_writer = ItemWriter(self._get_attribute)

    def run(self):
        """ Collect all mesh objects and writes their id, name and pose."""
        objects = []
        for object in get_all_mesh_objects():
            objects.append(object)

        self.write_attributes_to_file(self.object_writer, objects, "object_states_", "object_states",
                                      ["id", "name", "location", "rotation_euler", "matrix_world"])

    def _get_attribute(self, object, attribute_name):
        """ Returns the value of the requested attribute for the given object.

        :param object: The mesh object. Type: blender mesh type object.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """
        return super()._get_attribute(object, attribute_name)
