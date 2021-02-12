import os
import re
import math

import bpy

from src.loader.LoaderInterface import LoaderInterface
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
            "path": "/path/file.blend",     #<-------- path to a .blend file
            "load_from": "objects",         #<-------- datablock name/ID
            "entities": ".*abc.*"           #<-------- regular expression, load everything in the folder if not given
          }
        }

    Result: loading all objects of file.blend that match the pattern.

    Note:
    Some datablocks types like bpy.types.Light, bpy.types.Mesh, bpy.types.Camera etc are designed to be wrapped in 
    bpy.types.Object. Loading the container bpy.types.Object (represented as "objects" datablock here after) also loads the
    underlying datablocks. For example loading a Camera object of type bpy.types.Object wrapping underlying Camera bpy.types.Camera instance
    should load the instance as well but the converse is not true.

    For example only loading "cameras" i.e  bpy.types.Camera shall not load Animations,
    physical constraints and properties like location that are stored in the wrapper bpy.types.Object including properties. To load
    such objects its recommended to load the container "objects" datablocks and filter on entity name.


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
        * - load_from
          - The datablock or a list of datablocks which should be loaded from the given .blend file. Default: "objects"
            Available options are: ['armatures', 'cameras', 'curves', 'hairs', 'images', 'lights', 'materials', 'meshes', 'objects', 'textures']
          - string/list
        * - entities
          - Regular expression representing a name pattern of entities' (everything that can be stored in a .blend
            file's folders, see Blender's documentation for bpy.types.ID for more info) names. Optional.
          - string
        * - new_cam
    """
    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        # get a path to a .blend file
        path = Utility.resolve_path(self.config.get_string("path"))

        # Make sure we have a list of datablocks
        data_blocks = self.config.get_raw_value("load_from", "objects")
        if not isinstance(data_blocks, list):
            data_blocks = [data_blocks]
        # Make sure to also convert the old convention (e.q. /Object) to valid datablocks
        data_blocks = [(data_block.lower().strip("/") + ("s" if not data_block.endswith("s") else "")) for data_block in data_blocks]

        name_regrex = self.config.get_string("entities", "")
        # Start importing blend file. All objects that should be imported need to be copied from "data_from" to "data_to"
        with bpy.data.libraries.load(path) as (data_from, data_to):
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

        # Go over all imported objects again
        for data_block in data_blocks:
            if data_block == "objects":
                for obj in getattr(data_to, data_block):
                    # Link objects to the scene
                    bpy.context.collection.objects.link(obj)

                    # If a camera was imported
                    if obj.type == 'CAMERA':
                        # Make it the active camera in the scene
                        bpy.context.scene.camera = obj

                        # Find the maximum frame number of its key frames
                        max_keyframe = 0
                        fcurves = obj.animation_data.action.fcurves
                        for curve in fcurves:
                            keyframe_points = curve.keyframe_points
                            for keyframe in keyframe_points:
                                max_keyframe = max(max_keyframe, keyframe.co[0])

                        # Set frame_end to the next free keyframe
                        bpy.context.scene.frame_end = max_keyframe + 1