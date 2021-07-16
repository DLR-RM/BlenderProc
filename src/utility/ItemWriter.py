import numpy as np
from mathutils import Vector, Euler, Color, Matrix, Quaternion
import bpy
import json

from src.utility.MathUtility import MathUtility


class ItemWriter:

    def __init__(self, get_item_attribute_func):
        self.get_item_attribute_func = get_item_attribute_func

    def write_items_to_file(self, path_prefix, items, attributes, destination_frame):
        """ Writes the state of the given items to one numpy file per frame.

        :param path_prefix: The prefix path to write the files to.
        :param items: A list of items.
        :param attributes: A list of attributes to write per item.
        :param destination_frame: Used to transform points to the blender coordinate frame.
        """
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            bpy.context.scene.frame_set(frame)
            self._write_items_to_file_for_current_frame(path_prefix, items, attributes, frame, destination_frame)

    def _write_items_to_file_for_current_frame(self, path_prefix, items, attributes, frame, destination_frame):
        """ Writes the state of the given items to one numpy file for the given frame.

        :param path_prefix: The prefix path to write the files to.
        :param items: A list of items.
        :param attributes: A list of attributes to write per item.
        :param frame: The frame number.
        :param destination_frame: Used to transform points to the blender coordinate frame.
        """
        value_list = []
        # Go over all items
        for item in items:
            value_list_per_item = {}
            # Go through all attributes
            for attribute in attributes:
                # Get the attribute value
                value = self.get_item_attribute_func(item, attribute, destination_frame)

                # If its a list of numbers, just add to the array, else just add one value
                if isinstance(value, (Vector, Euler, Color, Quaternion)):
                    value = list(value)  
                elif isinstance(value, (Matrix, np.ndarray)):
                    value = np.array(value).tolist()

                if isinstance(value, list) and len(value) == 3:
                    MathUtility.change_coordinate_frame_of_point(value, destination_frame)

                value_list_per_item[attribute] = value

            value_list.append(value_list_per_item)

        # Write to a numpy file
        np.save(path_prefix + "%04d" % frame + ".npy", np.string_(json.dumps(value_list)))

