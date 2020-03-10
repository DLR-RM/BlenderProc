import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class ObjectLoader(Loader):
    """ Just imports the objects for the given file path

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "The path to the 3D data file to load. Can be either path or paths not both."
       "paths", "A list of paths of 3D data files to load. Can be either path or paths not both."
    """
    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        if self.config.has_param('path') and self.config.has_param('paths'):
            raise Exception("Objectloader can not use path and paths in the same module!")
        if self.config.has_param('path'):
            file_path = Utility.resolve_path(self.config.get_string("path"))
            loaded_objects = Utility.import_objects(filepath=file_path)
        elif self.config.has_param('paths'):
            file_paths = self.config.get_list('paths')
            loaded_objects = []
            # the file paths are mapped here to object names
            cache_objects = {}
            for file_path in file_paths:
                resolved_file_path = Utility.resolve_path(file_path)
                current_objects = Utility.import_objects(filepath=resolved_file_path, cached_objects=cache_objects)
                loaded_objects.extend(current_objects)
        else:
            raise Exception("Loader module needs either a path or paths config value")

        # Set the add_properties of all imported objects
        self._set_properties(loaded_objects)