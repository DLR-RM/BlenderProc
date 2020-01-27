
import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class ObjectLoader(Loader):
    """ Just imports the objects for the given file path

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "paths", "List of paths to the .obj files to be loaded."
       "add_properties", "List of of properties to add to the objects, or attributes to set."

    """
    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        files_paths = Utility.resolve_path(self.config.get_string("paths"))
        properties = Utility.get_dict(self.config.get_string("add_properties"))

        for path in files_paths:
            file_path = Utility.resolve_path(path)
            loaded_objects = Utility.import_objects(filepath=file_path)
            for obj in loaded_objects:
                for key in properties.keys():
                    if hasattr(obj, prop):
                        obj.key = properties[key]
                    else:
                        obj[key] = properties[key]

            # Set the physics property of all imported objects
            self._set_physics_property(loaded_objects)
