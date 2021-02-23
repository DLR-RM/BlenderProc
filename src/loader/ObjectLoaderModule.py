from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.loader.ObjectLoader import ObjectLoader


class ObjectLoaderModule(LoaderInterface):
    """ Just imports the objects for the given file path

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - path
          - The path to the 3D data file to load. Can be either path or paths not both.
          - string
        * - paths
          - A list of paths of 3D data files to load. Can be either path or paths not both.
          - list
    """
    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        if self.config.has_param('path') and self.config.has_param('paths'):
            raise Exception("Objectloader can not use path and paths in the same module!")
        if self.config.has_param('path'):
            file_path = Utility.resolve_path(self.config.get_string("path"))
            loaded_objects = ObjectLoader.load(filepath=file_path)
        elif self.config.has_param('paths'):
            file_paths = self.config.get_list('paths')
            loaded_objects = []
            # the file paths are mapped here to object names
            cache_objects = {}
            for file_path in file_paths:
                resolved_file_path = Utility.resolve_path(file_path)
                current_objects = ObjectLoader.load(filepath=resolved_file_path, cached_objects=cache_objects)
                loaded_objects.extend(current_objects)
        else:
            raise Exception("Loader module needs either a path or paths config value")

        if not loaded_objects:
            raise Exception("No objects have been loaded here, check the config.")

        # Set the add_properties of all imported objects
        self._set_properties(loaded_objects)
