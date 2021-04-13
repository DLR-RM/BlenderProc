import bpy

from src.utility.MeshObjectUtility import MeshObject
from typing import Union


class ObjectMerging:

    @staticmethod
    def merge_object_list(objects: Union[bpy.types.Object, MeshObject], merged_object_name: str = 'merged_object'):
        """ Generates an empty object and sets this as parent object for all objects in the list which do not already have a parent set.

        :param merged_object_name: The name of the parent object.
        """
        assert merged_object_name != "", "Parent object name cannot be empty!"
        print('name', merged_object_name)

        # create new empty object which acts as parent, and link it to the collection
        parent_obj = bpy.data.objects.new(merged_object_name, None)
        bpy.context.collection.objects.link(parent_obj)

        # select all relevant objects
        for obj in objects:
            # objects with a parent will be skipped, as this relationship will otherwise be broken
            # if a parent exists this object should be grandchild of parent_obj (or grandgrand...)
            if obj.parent is not None:
                continue
            # if the object doesn't have a parent we can set its parent
            obj.parent = parent_obj

        objects.append(parent_obj)
        return objects
