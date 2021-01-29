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

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Datablock
          - Description
          - Type
        * - Action
          - A collection of F-Curves for animation
          - bpy.types.Action
        * - Armature
          - Armature data-block containing a hierarchy of bones, usually used for rigging characters
          - bpy.types.Armature
        * - Brush
          - Brush data-block for storing brush settings for painting and sculpting
          - bpy.types.Brush
        * - CacheFile
          - Cache Files data-blocks
          - bpy.types.CacheFile
        * - Camera
          - Camera data-block for storing camera settings
          - bpy.types.Camera
        * - Collection
          - Collection of Object data-blocks
          - bpy.types.Collection
        * - Curve
          - Curve data-block storing curves, splines and NURBS
          - bpy.types.Curve
        * - FreestyleLineStyle
          - Freestyle line style, reusable by multiple line sets
          - bpy.types.FreestyleLineStyle
        * - GreasePencil
          - Freehand annotation sketchbook
          - bpy.types.GreasePencil
        * - Image
          - Image data-block referencing an external or packed image
          - bpy.types.Image
        * - Key
          - Shape keys data-block containing different shapes of geometric data-blocks
          - bpy.types.Key
        * - Lattice
          - Lattice data-block defining a grid for deforming other objects
          - bpy.types.Lattice
        * - Library
          - External .blend file from which data is linked
          - bpy.types.Library
        * - Light
          - Light data-block for lighting a scene
          - bpy.types.Light
        * - LightProbe
          - Light Probe data-block for lighting capture objects
          - bpy.types.LightProbe
        * - Mask
          - Mask data-block defining mask for compositing
          - bpy.types.Mask
        * - Material
          - Material data-block to define the appearance of geometric objects for rendering
          - bpy.types.Material
        * - Mesh
          - Mesh data-block defining geometric surfaces
          - bpy.types.Mesh
        * - MetaBall
          - Metaball data-block to defined blobby surfaces
          - bpy.types.MetaBall
        * - MovieClip
          - MovieClip data-block referencing an external movie file
          - bpy.types.MovieClip
        * - NodeTree
          - Node tree consisting of linked nodes used for shading, textures and compositing
          - bpy.types.NodeTree
        * - Object
          - Object data-block defining an object in a scene
          - bpy.types.Object
        * - PaintCurve
          - Paint Curves data-blocks
          - bpy.types.PaintCurve
        * - Palette
          - Palette data-blocks
          - bpy.types.Palette
        * - ParticleSettings
          - Particle settings, reusable by multiple particle systems
          - bpy.types.ParticleSettings
        * - Scene
          - Scene data-block, consisting in objects and defining time and render related settings
          - bpy.types.Scene
        * - Screen
          - Screen data-block, defining the layout of areas in a window
          - bpy.types.Screen
        * - Sound
          - Sound data-block referencing an external or packed sound file
          - bpy.types.Sound
        * - Speaker
          - Speaker data-block for 3D audio speaker objects
          - bpy.types.Speaker
        * - Text
          - Text data-block referencing an external or packed text file
          - bpy.types.Text
        * - Texture
          - Texture data-block used by materials, lights, worlds and brushes
          - bpy.types.Texture
        * - VectorFont
          - Vector font for Text objects
          - bpy.types.VectorFont
        * - Volume
          - Volume data-block for 3D volume grids
          - bpy.types.Volume
        * - WindowManager
          - Window manager data-block defining open windows and other user interface data
          - bpy.types.WindowManager
        * - WorkSpace
          - Workspace data-block, defining the working environment for the user
          - bpy.types.WorkSpace
        * - World
          - World data-block describing the environment and ambient lighting of a scene
          - bpy.types.World

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
                    
                for entity_to_load in entities_to_load:
                    # store already added entities of
                    # type attr_name
                    previous_objects = set(getattr(bpy.data, attr_name))

                    # load the new entity
                    bpy.ops.wm.append(
                        filepath=os.path.join(path, data_block_name, entity_to_load),
                        filename=entity_to_load,
                        directory=os.path.join(path, data_block_name))
                    

                    # get current entities of type attr_name
                    curr_objects = set(getattr(bpy.data, attr_name))

                    # get the newly added entity
                    added_resource = (curr_objects - previous_objects).pop()
                    
                    # if newly added entity is a camera, remove previous cameras
                    # and set current camera as active 
                    if hasattr(added_resource, 'type') and added_resource.type == 'CAMERA':
                        # remove previous cameras
                        for obj in previous_objects:
                            if hasattr(obj, 'type') and obj.type == 'CAMERA':
                                bpy.data.objects.remove(obj, do_unlink=True)

                        # add loaded camera
                        bpy.context.scene.collection.objects.link(added_resource)
                        bpy.context.scene.camera = added_resource
                        bpy.context.scene.frame_end = len(
                            self._get_camera_keyframes(added_resource))

                    self._set_properties([added_resource])
            else:
                raise Exception("Unsupported datablock/folder: {}\nSupported types:  {}".format( \
                                data_block_name, self.known_datablock_names))

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
            # match .blend file attributes to BlendData object
            # and find the type of those attributes. We can't
            # find it directly using blend_file_data because its
            # just string names.
            # For e.g bpy.data.nodes_group is collection of datablocks
            # of type bpy.type.NodeTree so we get get datablock name from attributes.
            # we need to match node_groups -> type NodeTree
            if hasattr(bpy.data, attr):
                relevant_blend_data = getattr(bpy.data, attr)
                # get type of the respective attribute of bpy.data.attr where
                # attr in (objects, meshes, lights, cameras etc)
                relevant_blend_data_type = relevant_blend_data.rna_type.identifier
                if data_block_name in relevant_blend_data_type:
                    index = i
                    break

        if index == -1:
            # The Datablock is valid but the .blend file does not contain the datablock. Likely
            # version not supported.
            raise Exception(
                "Could not match Datablock {} in the .blend file. please Verify that"
                "the .blend file version supports {} ID. CurrentBlender API Version {}"
                .format(data_block_name, data_block_name, bpy.app.version_string))

        return blend_file_datablock_names[index]

    def _get_camera_keyframes(self, camera):
        """
        Get Keyframes from animation data of a Camera Object.

        :param camera: The camera for which the keyframes are extracted
        :return: A list of keyframes
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
