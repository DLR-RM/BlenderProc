import bpy

from src.utility.ItemWriter import ItemWriter
from src.writer.WriterInterface import WriterInterface
from src.utility.BlenderUtility import get_all_mesh_objects

class ShapeNetWriter(WriterInterface):
    """ Writes the ShapeNet object attributes in an hdf5 file.
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

        shapenet_objects = [obj for obj in get_all_mesh_objects() if "used_synset_id" in obj]

        self.write_attributes_to_file(self.object_writer, shapenet_objects, "shapenet_", "shapenet", ["used_synset_id", "used_source_id"])

    def _get_attribute(self, shapenet_obj, attribute_name):
        """ Returns the value of the requested attribute for the given object.
        :param shapenet_obj: The ShapeNet object.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """

        if attribute_name == "used_synset_id":
            return shapenet_obj.get("used_synset_id", "")
        elif attribute_name == "used_source_id":
            return shapenet_obj.get("used_source_id", "")
        else:
            return super()._get_attribute(shapenet, attribute_name)
