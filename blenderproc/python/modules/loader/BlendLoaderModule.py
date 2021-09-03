from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.loader.BlendLoader import load_blend

class BlendLoaderModule(LoaderInterface):
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
          - Path to a .blend file. Can not be used with "paths".
          - string
        * - paths
          - A list of paths, each path must point to its own .blend file. Can not be used with "path".
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

    def run(self):
        if self.config.has_param("paths") and not self.config.has_param("path"):
            paths = self.config.get_list("paths")
            newly_loaded_objects = []
            for path in paths:
                newly_loaded_objects.extend(load_blend(
                    path=path,
                    obj_types=self.config.get_raw_value("obj_types", ['mesh', 'empty']),
                    name_regrex=self.config.get_string("entities", None),
                    data_blocks=self.config.get_raw_value("datablocks", "objects")
                ))
        elif self.config.has_param("path"):
            newly_loaded_objects = load_blend(
                path=self.config.get_string("path"),
                obj_types=self.config.get_raw_value("obj_types", ['mesh', 'empty']),
                name_regrex=self.config.get_string("entities", None),
                data_blocks=self.config.get_raw_value("datablocks", "objects")
            )
        else:
            if self.config.has_param("paths") and self.config.has_param("path"):
                raise Exception("Paths and path can not be used at the same time!")
            else:
                raise Exception("You need to specify the path of the .blend file you want to load.")
        self._set_properties([obj for obj in newly_loaded_objects if isinstance(obj, Entity)])
