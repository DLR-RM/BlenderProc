import numpy as np
from mathutils import Vector, Euler
import bpy
import json

class ItemWriter:

    def __init__(self, get_item_attribute_func):
        self.get_item_attribute_func = get_item_attribute_func

    def write_items_to_file(self, path_prefix, items, attributes):
        """ Writes the state of the given items to one numpy file per frame.

        :param path_prefix: The prefix path to write the files to.
        :param items: A list of items.
        :param attributes: A list of attributes to write per item.
        """
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            bpy.context.scene.frame_set(frame)
            self._write_items_to_file_for_current_frame(path_prefix, items, attributes, frame)

    def _write_items_to_file_for_current_frame(self, path_prefix, items, attributes, frame=None):
        """ Writes the state of the given items to one numpy file for the given frame.

        :param path_prefix: The prefix path to write the files to.
        :param items: A list of items.
        :param attributes: A list of attributes to write per item.
        :param frame: The frame number.
        """
        value_list = []
        # Go over all items
        for item in items:
            value_list_per_item = {}
            # Go through all attributes
            for attribute in attributes:
                # Get the attribute value
                value = self.get_item_attribute_func(item, attribute)

                # If its a list of numbers, just add to the array, else just add one value
                if isinstance(value, Vector) or isinstance(value, Euler):
                    value = list(value)

                value_list_per_item[attribute] = value

            value_list.append(value_list_per_item)

        # Write to a numpy file
        np.save(path_prefix + "%04d" % frame + ".npy", np.string_(json.dumps(value_list)))

