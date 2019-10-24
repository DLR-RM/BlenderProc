from src.main.Module import Module
from src.utility.ItemWriter import ItemWriter
import bpy
import os

class StateWriter(Module):
    """ Writes the state of multiple items for each frame to a file.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "attributes_to_write", "A list of attribute names that should written to file. The next table lists all attributes that can be used here"
       "output_file_prefix", "The prefix of the file that should be created."
       "output_key", "The key which should be used for storing the output in a merged file."

    **Attributes per object**:

    .. csv-table::
       :header: "Keyword", "Description"

       "id", "A unique id."
       "location", "The location of the item (x, y and z coordinate)."
       "rotation_euler", "The rotation of the item written as three euler angles."
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.name_to_id = {}

    def write_attributes_to_file(self, item_writer, items, default_file_prefix, default_output_key):
        """ Writes the state of the given items to a file with the configured prefix.

        This method also registers the corresponding output.

        :param item_writer: The item writer object to use.
        :param items: The list of items.
        :param default_file_prefix: The default file name prefix to use.
        :param default_output_key: The default output key to use.
        """
        file_prefix = self.config.get_string("output_file_prefix", default_file_prefix)
        path_prefix = os.path.join(self._determine_output_dir(), file_prefix)

        item_writer.write_items_to_file(path_prefix, items, self.config.get_list("attributes_to_write"))

        self._register_output(file_prefix, self.config.get_string("output_key", default_output_key), ".npy", "1.0.0")

    def _get_attribute(self, item, attribute_name):
        """ Returns the value of the requested attribute for the given item.

        This method covers all general attributes that blender objects have.

        :param item: The item, has to be a blender object.
        :param attribute_name: The attribute name.
        :return: The attribute value.
        """
        if attribute_name == "id":
            if item.name not in self.name_to_id:
                self.name_to_id[item.name] = len(self.name_to_id.values())
            return self.name_to_id[item.name]
        elif attribute_name == "location":
            return item.location
        elif attribute_name == "rotation_euler":
            return item.rotation_euler
        else:
            raise Exception("No such attribute: " + attribute_name)
