import os
import re

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility


class BlendLoader(LoaderInterface):
    """
    This class provides functionality to load entities from a .blend file. A .blend file is a 
    blender generated  data file that wraps project resources into sections/datablocks. Resources can be
    loaded individually by name pattern matching or entire datablocks to entire project. For more
    information about a datablock see Blender's documentation for bpy.types.ID. 

    Sections/Datablocks in a .blend File
    +-------------------+
    |    Blend File     |
    +-------------------+
    |    Collections    |
    |    Object         |
    |    Mesh           |
    |    Text           |
    |    Scene          |
    |    World          |
    |    Workspace      |
    |    Curve          |
    |    Camera         |
    |    Light          |
    |    Material       |
    |    Texture        |
    |    ......         |
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
        self.known_datablock_names = [cls.__name__ for cls in bpy.types.ID.__subclasses__()]

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

        with bpy.data.libraries.load(path) as (blend_file_data, data_to):
            self.blend_file_version = [lib.version for lib in bpy.data.libraries if lib.filepath == path]
            data_block_name = load_from.strip("/")

            # check if defined ID is supported
            if data_block_name in  self.known_datablock_names:
                attr_name = self._find_datablock_name_match_in_blendfile(blend_file_data, data_block_name)

                # if some regex was specified, get corresponding matching entity's names
                if entities is not None:
                    entities_to_load = [item for item in getattr(blend_file_data, attr_name)
                                        if re.fullmatch(entities, item) is not None]
                # get all entity's names if not
                else:
                    entities_to_load = getattr(blend_file_data, attr_name)
                # load entities
                for entity_to_load in entities_to_load:
                    bpy.ops.wm.append(filepath=os.path.join(path, load_from, entity_to_load),
                                      filename=entity_to_load,
                                      directory=os.path.join(path + load_from))

                    #exec("added_resource = bpy.data.{}['{}']".format(attr_name, entity_to_load))
                    added_resource = getattr(bpy.data, attr_name)[entity_to_load]
                    
                    # setup proeprties. For Mesh based Objects use LoaderInterface._set_properties
                    # that expects a mesh object and sets the polygon of the mesh to smooth/non smooth
                    # Non mesh based objects dont have polygons.
                    if hasattr(added_resource, 'type') and added_resource.type == 'MESH':
                        self._set_properties([added_resource])
                    else:
                        # Non Mesh based object like Light, Camera wrapepd in objects
                        # or non wrappable objects like materials, textures
                        self._set_datablock_properties(added_resource)
            else:
                raise Exception("Unsupported datablock/folder name: " + load_from +
                                "\nSupported names: " + str(self.known_datablock_names.keys()) +
                                "\nIf your ID exists, but not supported, please append a new pair of "
                                "{type ID(folder name): parameter name} to the 'known_datablock_names' dict. Use this "
                                "for finding your parameter name: " + str(dir(data_from)))

    def _find_datablock_name_match_in_blendfile(self, blend_file_data, data_block_name):
        """
        Finds the corresponding datablock name in loaded .blend file.
        .blend file uses slightly different string name for Datablocks, includes
        underscores and extra s/'es'. For example /Mesh datablock name is matched to 
        meshes attribute of .blend file. GreasePencil is matched to grease_pencils and so on.

        :param blend_file_data: contents of loaded .blend file
        :param data_block_name: Datablock name of a .blend file
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
                             Blender API Version {}".format(data_block_name, data_block_name, bpy.app.version_string))

        return blend_file_datablock_names[index]

    def _set_datablock_properties(self, resource):
        """
        Sets the custom properties of **non object** resources like materials,
        textures, images, etc.

        Note: Some datablock types like bpy.types.Light, bpy.types.Mesh, bpy.types.Camera etc
        are wrapped in bby.types.Object which act as a container of these object. In that case
        setting the properties of the container object does not set the properties of underlying datablock like
        camera and vice versa. Setting the bpy.data.objects["Light"] and bpy.data.lights["light"] can
        have different properties. This function sets properties of all types materials, lights,
        cameras even if they are loaded as an object. For Objects that wraps Meshes use  self._set_properties
        instead
        """
        properties = self.config.get_raw_dict("add_properties", {})
        for key, value in properties.items():
            resource[key] = value           