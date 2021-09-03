from blenderproc.python.modules.utility.ItemWriter import ItemWriter
from blenderproc.python.modules.writer.WriterInterface import WriterInterface
from blenderproc.python.writer.WriterUtility import WriterUtility
from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects

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
        self.object_writer = ItemWriter(WriterUtility._get_shapenet_attribute)

    def run(self):
        """ Collect ShapeNet attributes and write them to a file."""

        shapenet_objects = [obj for obj in get_all_blender_mesh_objects() if "used_synset_id" in obj]

        self.write_attributes_to_file(self.object_writer, shapenet_objects, "shapenet_", "shapenet", ["used_synset_id", "used_source_id"])


