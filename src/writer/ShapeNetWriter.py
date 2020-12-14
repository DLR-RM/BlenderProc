import bpy

from src.utility.ItemWriter import ItemWriter
from src.writer.WriterInterface import WriterInterface
from src.utility.BlenderUtility import get_all_mesh_objects

class ShapeNetWriter(WriterInterface):
    """ Writes the state of all camera poses to a numpy file, if there was no hdf5 file to add them to.
    **Attributes per object**:
    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1
        * - Parameter
          - Description
          - Type
        * - synset_id
          - The synset noun offset in WordNet (http://wordnetweb.princeton.edu/perl/webwn3.0)
          - string
        * - source_id
          - The identifier of the original model on the online repository from which it was collected to build the ShapeNet dataset.
          - string
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        self.object_writer = ItemWriter(self._get_attribute)

    def run(self):
        """ Collect ShapeNet attributes and write them to a file."""

        for object in get_all_mesh_objects():
            used_synset_id = object.get("used_synset_id", "")
            used_source_id = object.get("used_source_id", "")

        shapenet_attributes = (used_synset_id, used_source_id)
        self.write_attributes_to_file(self.object_writer, [shapenet_attributes], "shapenet_", "shapenet", ["used_synset_id", "used_source_id"])

    def _get_attribute(self, shapenet, attribute_name):
        """ Returns the value of the requested attribute for the given object.
        :param shapenet: The ShapeNet object.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """
        used_synset_id, used_source_id = shapenet

        if attribute_name == "used_synset_id":
            return used_synset_id
        elif attribute_name == "used_source_id":
            return used_source_id
        else:
            return super()._get_attribute(shapenet, attribute_name)

