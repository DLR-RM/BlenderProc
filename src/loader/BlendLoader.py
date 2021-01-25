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

    Sections/Datablocks in a .blend File

    +-------------------+
    |    .Blend File    |
    +===================+
    |    Collections    |
    +-------------------+
    |    Object         |
    +-------------------+
    |    Mesh           |
    +-------------------+
    |    Text           |
    +-------------------+
    |    Scene          |
    +-------------------+
    |    World          |
    +-------------------+
    |    Workspace      |
    +-------------------+
    |    Curve          |
    +-------------------+
    |    Camera         |
    +-------------------+
    |    Light          |
    +-------------------+
    |    Material       |
    +-------------------+
    |    Texture        |
    +-------------------+
    |    more...        |
    +-------------------+


    Example:

    .. code-block:: yaml

        {
          "module": "loader.BlendLoader",
          "config": {
            "path": "/path/file.blend",     #<-------- path to a .blend file
            "load_from": "/Object",         #<-------- folder name/ID: /Collection, /Texture, /Material, etc.
            "entities": ".*abc.*"           #<-------- regular expression, load everything in the folder if not given
          }
        }

    Result: loading all objects from folder /Object of file.blend that match the pattern.

    Note:
    Some datablocks types like bpy.types.Light, bpy.types.Mesh, bpy.types.Camera etc are designed to be wrapped in 
    bpy.types.Object. Loading the container bpy.types.Object (represented as /Object datablock here after) also loads the
    underlying datablocks. For example loading a Camera object of type bpy.types.Object wrapping underlying Camera bpy.types.Camera instance
    should load the instance as well but the converse is not true.

    For example only loading a ./Camera i.e  bpy.types.Camera shall not load Animations, 
    physical constraints and properties like location that are stored in the wrapper bpy.types.Object including properties. To load
    such objects its recommended to load the container /Object datablocks and filter on entity name.


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
          - Name of the datablock/folder inside .blend file. Always start with '/'. See known_datablock_names for
            supported folder names/type IDs.
          - string
        * - entities
          - Regular expression representing a name pattern of entities' (everything that can be stored in a .blend
            file's folders, see Blender's documentation for bpy.types.ID for more info) names. Optional.
          - string
    """
    def __init__(self, config):
        LoaderInterface.__init__(self, config)
        # Supported Datablocks types by Blender Python API
        self.known_datablock_names = [
            cls.__name__ for cls in bpy.types.ID.__subclasses__()
        ]

    def run(self):
        """
        1 - Loads a .blend file
        2 - Search the file for matching datablock in the .blend file
        3 - Append the datablocks to current bpy.data
        4 - Set Properties of the datablock resource after its
            appended to current environment.
        """
        # get a path to a .blend file
        path = Utility.resolve_path(self.config.get_string("path"))

        # get section name/Blend ID
        load_from = self.config.get_string("load_from")
        # get a entities' name regex if present, set to None if not
        if self.config.has_param("entities"):
            entities = self.config.get_string("entities")
        else:
            entities = None
        
        data_block_name = load_from.strip("/")

        with bpy.data.libraries.load(path) as (blend_file_data, _):
            # check if defined ID is supported
            if data_block_name in self.known_datablock_names:
                attr_name = self._find_datablock_name_match_in_blendfile(
                    blend_file_data, data_block_name)

                # if some regex was specified, get corresponding matching entity's names
                if entities is not None:
                    entities_to_load = [
                        item for item in getattr(blend_file_data, attr_name)
                        if re.fullmatch(entities, item) is not None
                    ]

                # get all entity's names if not
                else:
                    entities_to_load = getattr(blend_file_data, attr_name)
                # load entities
                for entity_to_load in entities_to_load:

                    # remove the earlier existing resource with same name
                    if entity_to_load in bpy.data.objects:
                        bpy.data.objects.remove(bpy.data.objects[entity_to_load], do_unlink=True)

                    bpy.ops.wm.append(filepath=os.path.join( path, data_block_name, entity_to_load),
                                      filename=entity_to_load,
                                      directory=os.path.join(path, data_block_name))

                    added_resource = getattr(bpy.data, attr_name)[entity_to_load]

                    if hasattr(added_resource, 'type') and added_resource.type == 'CAMERA':
                        bpy.context.scene.collection.objects.link(
                            added_resource)
                        bpy.context.scene.camera = added_resource
                        bpy.context.scene.frame_end = len(
                            self._get_camera_keyframes(added_resource))

                    self._set_properties([added_resource])
            else:
                raise Exception(
                    "Unsupported datablock/folder name: {}\nSupported names:  {}\n \
                     If your ID exists, but not supported, please append a new pair of "
                    "{type ID(folder name): parameter name} to the 'known_datablock_names' dict. Use this "
                    "for finding your parameter name: {}".format(
                        str(data_block_name, self.known_datablock_names.keys()), data_block_name))

    def _find_datablock_name_match_in_blendfile(self, blend_file_data,
                                                data_block_name):
        """
        Finds the corresponding datablock name in loaded .blend file.
        .blend file uses slightly different string name for Datablocks, includes
        underscores and extra s/'es'. For example /Mesh datablock name is matched to 
        meshes attribute of .blend file. GreasePencil is matched to grease_pencils and so on.

        :param blend_file_data: contents of loaded .blend file
        :param data_block_name: Datablock name of a .blend file
        :return: Name of the matching section for the probvided datablock
        in the .blend file
        """
        blend_file_datablock_names = dir(blend_file_data)
        index = -1
        for i, attr in enumerate(blend_file_datablock_names):
            # remove underscores like grease_pencils -> greasepencils and match with GreasePencil
            # datablock
            attr = attr.replace('_', '')
            if data_block_name.lower() in attr:
                index = i
                break

        if index == -1:
            # The Datablock is valid but the .blend file does not contain the datablock. Likely
            # version not supported.
            raise Exception("Could not match Datablock {} in the .blend file. please Verify that \
                            the .blend file version supports {} ID. Current \
                            Blender API Version {}".format(
                    data_block_name, data_block_name, bpy.app.version_string))

        return blend_file_datablock_names[index]

    def _get_camera_keyframes(self, camera):
        """
        Get Keyframes from animation data of a Camera Object.

        :param camera: The camera for which the keyframes are extracted
        :return: [] keyframes
        """
        keyframes = []

        # get camera animation data
        anim = camera.animation_data
        if anim is not None and anim.action is not None:
            # The animation change over time of an object is represented by
            # F-curve, which is part of an object's action data. 
            # Link: https://docs.blender.org/manual/en/latest/editors/graph_editor/fcurves/introduction.html
            # Go over all the variables involved in the animation
            # for example for animation of translation in 3D, 
            # we shall have fcurve for each variable x,y,z.
            for fcu in anim.action.fcurves:
                # go over all the keyframes (bpy.types.FCurveKeyframePoints) for a variable, 
                # and see how it changes its value per keyframe
                for keyframe in fcu.keyframe_points:

                    #  a keyframe has form (frame number, value of current variable in that frame).
                    frame, value = keyframe.co
                    if frame not in keyframes:
                        # frame numbers are in range (float [-inf, inf])
                        # for example x coordinats of camera at frame 1.8
                        # is 1.2, at frame 1.9 it can be 1.3 and so on, we would
                        # get varous values between two frames, but we need 
                        # total unique frames in an animation not total
                        # number of values of animation so we round of
                        # frame numbers and store unique frames.
                        keyframes.append((math.ceil(frame)))
        return keyframes
