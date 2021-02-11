from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.loader.BlendLoader import BlendLoader

class BlendLoaderModule(LoaderInterface):
    """
    Loads entities (everything that can be stored in a .blend file's folders, see Blender's documentation for
    bpy.types.ID for more info) that match a name pattern from a specified .blend file's section/datablock.


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
        # supported pairs of {ID type/section names: datablock parameter names}
        self.known_datablock_names = {"/Camera": "cameras",
                                      "/Collection": "collections",
                                      "/Image": "images",
                                      "/Light": "lights",
                                      "/Material": "materials",
                                      "/Mesh": "meshes",
                                      "/Object": "objects",
                                      "/Texture": "textures"}

    def run(self):
        # get a path to a .blend file
        path = Utility.resolve_path(self.config.get_string("path"))
        # get section name/Blend ID
        load_from = self.config.get_string("load_from")
        # get a entities' name regex if present, set to None if not
        if self.config.has_param("entities"):
            entities = self.config.get_string("entities")
        else:
            entities = None

        newly_loaded_objects = BlendLoader.load(path, load_from, entities)
        self._set_properties(newly_loaded_objects)
