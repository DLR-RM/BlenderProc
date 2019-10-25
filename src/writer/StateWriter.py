from src.main.Module import Module
from src.utility.ItemWriter import ItemWriter
import bpy
import os
import mathutils

from src.utility.Utility import Utility


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
        self.destination_frame = self.config.get_list("destination_frame", ["X", "Y", "Z"])

    def write_attributes_to_file(self, item_writer, items, default_file_prefix, default_output_key, default_attributes, version="1.0.0"):
        """ Writes the state of the given items to a file with the configured prefix.

        This method also registers the corresponding output.

        :param item_writer: The item writer object to use.
        :param items: The list of items.
        :param default_file_prefix: The default file name prefix to use.
        :param default_output_key: The default output key to use.
        :param default_attributes: The default attributes to write, if no attributes are specified in the config.
        :param version: The version to use when registering the output.
        """
        file_prefix = self.config.get_string("output_file_prefix", default_file_prefix)
        path_prefix = os.path.join(self._determine_output_dir(), file_prefix)

        item_writer.write_items_to_file(path_prefix, items, self.config.get_list("attributes_to_write", default_attributes))

        self._register_output(file_prefix, self.config.get_string("output_key", default_output_key), ".npy", version)

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
            return Utility.transform_point_to_blender_coord_frame(item.location, self.destination_frame)
        elif attribute_name == "rotation_euler":
            return Utility.transform_point_to_blender_coord_frame(item.rotation_euler, self.destination_frame)
        elif attribute_name == "rotation_forward_vec":
            # Calc forward vector from rotation matrix
            rot_mat = item.rotation_euler.to_matrix()
            forward = rot_mat @ mathutils.Vector([0, 0, -1])
            return Utility.transform_point_to_blender_coord_frame(forward, self.destination_frame)
        elif attribute_name == "rotation_up_vec":
            # Calc up vector from rotation matrix
            rot_mat = item.rotation_euler.to_matrix()
            up = rot_mat @ mathutils.Vector([0, 1, 0])
            return Utility.transform_point_to_blender_coord_frame(up, self.destination_frame)
        elif attribute_name.startswith("customprop_"):
            custom_property_name = attribute_name[len("customprop_"):]
            # Make sure the requested custom property exist
            if custom_property_name in item:
                return item[custom_property_name]
            else:
                raise Exception("No such custom property: " + custom_property_name)
        else:
            raise Exception("No such attribute: " + attribute_name)
