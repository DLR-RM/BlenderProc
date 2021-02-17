import os
import re
import math
from typing import Union

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.BlenderUtility import collect_all_orphan_datablocks
from src.utility.Utility import Utility


class BlendLoader(LoaderInterface):
    """
    This class provides functionality to load entities from a .blend file. A .blend file is a 
    blender generated  data file that wraps project resources into sections/datablocks. Resources can be
    loaded individually by name pattern matching or entire datablocks to entire project. For more
    information about a datablock see Blender's documentation for bpy.types.ID
    at https://docs.blender.org/api/current/bpy.types.ID.html

    Example:

    .. code-block:: yaml

        {
          "module": "loader.BlendLoader",
          "config": {
            "path": "/path/file.blend",              #<-------- path to a .blend file
            "datablocks": ["objects", "materials"],  #<-------- datablock name/ID
            "obj_types": ["mesh"],                   #<-------- object types
            "entities": ".*abc.*"                    #<-------- regular expression, load everything in the folder if not given
          }
        }

    Result: loading all mesh objects and materials of file.blend that match the pattern.

    The datablock type "objects" means mesh objects as well as camera and light objects.
    To further specify which object types exactly should be loaded, the parameter "object_types" exists.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - path
          - Path to a .blend file.
          - string
        * - obj_types
          - The type of objects to load. This parameter is only relevant when `datablocks` is set to `"objects"`. Default: ['mesh', 'empty']
            Available options are: ['mesh', 'curve', 'hair', 'armature', 'empty', 'light', 'camera']
          - string/list
        * - entities
          - Regular expression representing a name pattern of entities' (everything that can be stored in a .blend
            file's folders, see Blender's documentation for bpy.types.ID for more info) names. Optional.
          - string
        * - datablocks
          - The datablock or a list of datablocks which should be loaded from the given .blend file. Default: "objects"
            Available options are: ['armatures', 'cameras', 'curves', 'hairs', 'images', 'lights', 'materials', 'meshes', 'objects', 'textures']
          - string/list
    """
    def __init__(self, config):
        LoaderInterface.__init__(self, config)
        self.valid_datablocks = [collection.lower() for collection in dir(bpy.data) if isinstance(getattr(bpy.data, collection), bpy.types.bpy_prop_collection)]
        self.valid_object_types = ['mesh', 'curve', 'surface', 'meta', 'font', 'hair', 'pointcloud', 'volume', 'gpencil', 'armature', 'lattice', 'empty', 'light', 'light_probe', 'camera', 'speaker']

        # get a path to a .blend file
        self.path = Utility.resolve_path(self.config.get_string("path"))

        self.data_blocks = self._validate_and_standardizes_configured_list(self.config.get_raw_value("datablocks", "objects"), self.valid_datablocks, "data block")
        self.obj_types = self._validate_and_standardizes_configured_list(self.config.get_raw_value("obj_types", ['mesh', 'empty']), self.valid_object_types, "object type")

    def _validate_and_standardizes_configured_list(self, config_value: Union[list, str], allowed_elements: list, element_name: str) -> list:
        """ Makes sure the given config value is a list, is lower case and only consists of valid elements.

        :param config_value: The configured value that should be standardized and validated.
        :param allowed_elements: A list of valid elements. If one configured element is not contained in this list an exception is thrown.
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

    def run(self):
        # Remember which orphans existed beforehand
        orphans_before = collect_all_orphan_datablocks()

        name_regrex = self.config.get_string("entities", "")
        # Start importing blend file. All objects that should be imported need to be copied from "data_from" to "data_to"
        with bpy.data.libraries.load(self.path) as (data_from, data_to):
            for data_block in self.data_blocks:
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

        # Go over all imported objects again
        for data_block in self.data_blocks:
            # Some adjustments that only affect objects
            if data_block == "objects":
                loaded_objects = []
                for obj in getattr(data_to, data_block):
                    # Check that the object type is desired
                    if obj.type.lower() in self.obj_types:
                        # Link objects to the scene
                        bpy.context.collection.objects.link(obj)
                        loaded_objects.append(obj)

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
                loaded_objects = getattr(data_to, data_block)
            # Set custom properties to all added objects
            self._set_properties(loaded_objects)

        # As some loaded objects were deleted again due to their type, we need also to remove the dependent datablocks that were also loaded and are now orphans
        self.purge_added_orphans(orphans_before, data_to)

    def purge_added_orphans(self, orphans_before, data_to):
        """ Removes all orphans that did not exists before loading the blend file.

        :param orphans_before: A dict of sets containing orphans of all kind of datablocks that existed before loading the blend file.
        :param data_to: The list of objects that were loaded on purpose and should not be removed, even when they are orphans.
        """
        purge_orphans = True
        while purge_orphans:
            purge_orphans = False
            orphans_after = collect_all_orphan_datablocks()
            # Go over all datablock types
            for collection_name in orphans_after.keys():
                # Go over all orphans of that type that were added due to this loader
                for orphan in orphans_after[collection_name].difference(orphans_before[collection_name]):
                    # Check whether this orphan was loaded on purpose
                    if orphan not in getattr(data_to, collection_name):
                        # Remove the orphan
                        getattr(bpy.data, collection_name).remove(orphan)
                        # Make sure to run the loop again, so we can detect newly created orphans
                        purge_orphans = True