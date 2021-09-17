from typing import List

from blenderproc.python.types.EntityUtility import Entity, create_empty


def merge_objects(objects: List[Entity], merged_object_name: str = 'merged_object') -> Entity:
    """ Generates an empty object and sets this as parent object for all objects in the list which do not already have a parent set.

    :param objects: A list of objects to be merged.
    :param merged_object_name: The name of the parent object.
    """
    assert merged_object_name != "", "Parent object name cannot be empty!"
    print('name', merged_object_name)

    # create new empty object which acts as parent, and link it to the collection
    parent_obj = create_empty(merged_object_name)

    # select all relevant objects
    for obj in objects:
        # objects with a parent will be skipped, as this relationship will otherwise be broken
        # if a parent exists this object should be grandchild of parent_obj (or grandgrand...)
        if obj.get_parent() is not None:
            continue
        # if the object doesn't have a parent we can set its parent
        obj.set_parent(parent_obj)

    return parent_obj
