"""Loading the content of .blend files"""

import re
import os
import collections
from typing import List, Dict, Tuple, Union, Optional

import bpy

from blenderproc.python.utility.BlenderUtility import collect_all_orphan_data_blocks
from blenderproc.python.types.EntityUtility import Entity, convert_to_entity_subclass
from blenderproc.python.utility.Utility import Utility, resolve_path


def record_hierarchy(path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Backup already set up scene, open blend file, store it's hierarchy and restore original scene.

    Hierarchy cannot be read by just loading the library, the scene needs to be open to access it.
    This approach is easier than resetting up already set up scene.
    :param path: Path to a .blend file.
    :return: Tuple of two dictionaries, one with collection and list of its children and one with
    object and list of collections it belongs to.
    """
    temp_filepath = os.path.join(Utility.get_temporary_directory(), "temp.blend")
    bpy.ops.wm.save_as_mainfile(filepath=temp_filepath)
    bpy.ops.wm.open_mainfile(filepath=path)

    collection_hierarchy = {}
    object_collections_hierarchy = collections.defaultdict(list)

    for coll in bpy.data.collections:
        collection_hierarchy[coll.name] = [c.name for c in coll.children]
        for obj in coll.objects:
            object_collections_hierarchy[obj.name].append(coll.name)

    bpy.ops.wm.open_mainfile(filepath=temp_filepath)
    os.remove(temp_filepath)

    return collection_hierarchy, object_collections_hierarchy

def build_collection_hierarchy(collection_hierarchy: Dict[str, List[str]]):
    """
    Recreate collection hierarchy from source blend

    :param collection_hierarchy: Dictionary of collection names and list oif their children names
    """

    root = bpy.context.scene.collection
    for coll in collection_hierarchy:
        new_coll = bpy.data.collections.new(coll)
        root.children.link(new_coll)

    for coll, children in collection_hierarchy.items():
        for child in children:
            child_coll = bpy.data.collections.get(child)
            bpy.data.collections.get(coll).children.link(child_coll)
            root.children.unlink(child_coll)

def add_obj_to_hierarchy(obj: bpy.types.Object, object_collections_hierarchy: Dict[str, List[str]]):
    """
    Add object to collection of same name as the one in source blend

    :param collection_hierarchy: Dictionary of collection names and list oif their children names
    """
    collection_parents = object_collections_hierarchy.get(obj.name)
    if collection_parents is None:
        bpy.context.collection.objects.link(obj)
    else:
        for parent in collection_parents:
            coll = bpy.data.collections.get(parent)
            assert coll is not None
            coll.objects.link(obj)

def load_blend(path: str, obj_types: Optional[Union[List[str], str]] = None, name_regrex: Optional[str] = None,
               data_blocks: Union[List[str], str] = "objects", link: bool = False, store_hierarchy: bool = False) -> List[Entity]:
    """
    Loads entities (everything that can be stored in a .blend file's folders, see Blender's documentation for
    bpy.types.ID for more info) that match a name pattern from a specified .blend file's section/data_block.

    :param path: Path to a .blend file.
    :param obj_types: The type of objects to load. This parameter is only relevant when `data_blocks`
                      is set to `"objects"`. Available options are: ['mesh', 'curve', 'hair', 'armature',
                      'empty', 'light', 'camera']
    :param name_regrex: Regular expression representing a name pattern of entities' (everything that can be
                        stored in a .blend file's folders, see Blender's documentation for bpy.types.ID
                        for more info) names.
    :param data_blocks: The data block or a list of data blocks which should be loaded from the given .blend file.
                        Available options are: ['armatures', 'cameras', 'curves', 'hairs', 'hair_curves', 'images',
                        'lights', 'materials', 'meshes', 'objects', 'textures']
    :param link: whether to link instead of append data blocks from .blend file. Linked objects can not be modified.
    :param store_hierarchy: Maintain top-level hierarchy from scene provided by path param.
    :return: The list of loaded mesh objects.
    """
    if obj_types is None:
        obj_types = ["mesh", "empty"]
    # get a path to a .blend file
    path = resolve_path(path)
    data_blocks = _BlendLoader.validate_and_standardizes_configured_list(data_blocks, _BlendLoader.valid_data_blocks,
                                                                         "data block")
    obj_types = _BlendLoader.validate_and_standardizes_configured_list(obj_types, _BlendLoader.valid_object_types,
                                                                       "object type")

    # Remember which orphans existed beforehand
    orphans_before = collect_all_orphan_data_blocks()

    if store_hierarchy:
        collection_hierarchy, object_collections_hierarchy = record_hierarchy(path)

    # Start importing blend file. All objects that should be imported need to be copied from "data_from" to "data_to"
    with bpy.data.libraries.load(path, link=link) as (data_from, data_to):
        for data_block in data_blocks:
            # Verify that the given data block is valid
            if hasattr(data_from, data_block):
                # Find all entities of this data block that match the specified pattern
                data_to_entities = []
                for entity_name in getattr(data_from, data_block):
                    if not name_regrex or re.fullmatch(name_regrex, entity_name) is not None:
                        data_to_entities.append(entity_name)
                # Import them
                setattr(data_to, data_block, data_to_entities)
                print("Imported " + str(len(data_to_entities)) + " " + data_block)
            else:
                raise Exception("No such data block: " + data_block)

    if store_hierarchy:
        build_collection_hierarchy(collection_hierarchy)

    # Go over all imported objects again
    loaded_objects: List[Entity] = []
    for data_block in data_blocks:
        # Some adjustments that only affect objects
        if data_block == "objects":
            for obj in getattr(data_to, data_block):
                # Check that the object type is desired
                if obj.type.lower() in obj_types:
                    loaded_objects.append(convert_to_entity_subclass(obj))
                    if store_hierarchy:
                        add_obj_to_hierarchy(obj, object_collections_hierarchy)
                    else:
                        bpy.context.collection.objects.link(obj)

                    # If a camera was imported
                    if obj.type == 'CAMERA':
                        # Make it the active camera in the scene
                        bpy.context.scene.camera = obj

                        # Find the maximum frame number of its key frames
                        max_keyframe = -1
                        if obj.animation_data is not None:
                            fcurves = obj.animation_data.action.fcurves
                            for curve in fcurves:
                                keyframe_points = curve.keyframe_points
                                for keyframe in keyframe_points:
                                    max_keyframe = max(max_keyframe, keyframe.co[0])

                        # Set frame_end to the next free keyframe
                        bpy.context.scene.frame_end = max_keyframe + 1
                else:
                    # Remove object again if its type is not desired
                    bpy.data.objects.remove(obj, do_unlink=True)
            print("Selected " + str(len(loaded_objects)) + " of the loaded objects by type")
        else:
            loaded_objects.extend(getattr(data_to, data_block))

    # As some loaded objects were deleted again due to their type, we need also to remove the dependent
    # data blocks that were also loaded and are now orphans
    _BlendLoader.purge_added_orphans(orphans_before, data_to)
    return loaded_objects


class _BlendLoader:
    valid_data_blocks = [collection.lower() for collection in dir(bpy.data) if
                        isinstance(getattr(bpy.data, collection), bpy.types.bpy_prop_collection)]
    valid_object_types = ['mesh', 'curve', 'curves', 'surface', 'meta', 'font', 'hair', 'pointcloud', 'volume',
                          'gpencil', 'armature', 'lattice', 'empty', 'light', 'light_probe', 'camera', 'speaker']

    @staticmethod
    def validate_and_standardizes_configured_list(config_value: Union[list, str], allowed_elements: list,
                                                  element_name: str) -> list:
        """ Makes sure the given config value is a list, is lower case and only consists of valid elements.

        :param config_value: The configured value that should be standardized and validated.
        :param allowed_elements: A list of valid elements. If one configured element is not contained in this list
                                 an exception is thrown.
        :param element_name: How one element is called. Used to create an error message.
        :return: The standardized and validated config value.
        """
        # Make sure we have a list
        if not isinstance(config_value, list):
            config_value = [config_value]
        config_value = [element.lower() for element in config_value]

        # Check that the given elements are valid
        for element in config_value:
            if element not in allowed_elements:
                raise Exception("No such " + element_name + ": " + element)

        return config_value

    @staticmethod
    def purge_added_orphans(orphans_before, data_to):
        """ Removes all orphans that did not exists before loading the blend file.

        :param orphans_before: A dict of sets containing orphans of all kind of data_blocks that existed before
                               loading the blend file.
        :param data_to: The list of objects that were loaded on purpose and should not be removed, even when
                        they are orphans.
        """
        purge_orphans = True
        while purge_orphans:
            purge_orphans = False
            orphans_after = collect_all_orphan_data_blocks()
            # Go over all data_block types
            for collection_name, orphan_block in orphans_after.items():
                # Go over all orphans of that type that were added due to this loader
                for orphan in orphan_block.difference(orphans_before[collection_name]):
                    # Check whether this orphan was loaded on purpose
                    if orphan not in getattr(data_to, collection_name):
                        # Remove the orphan
                        getattr(bpy.data, collection_name).remove(orphan)
                        # Make sure to run the loop again, so we can detect newly created orphans
                        purge_orphans = True
