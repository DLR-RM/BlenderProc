
import bpy
import os
from src.loader.Loader import Loader
from src.main.Module import Module
from src.utility.Utility import Utility


class IkeaObjectsLoader(Loader):
    """ Imports ikea object file straight into blender, and hides it

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "category", "Category of the objects in the scene that those ikea objects are to replace."
       "paths", "List of paths to the .obj files to be loaded."
    """
    def __init__(self, config):
        Loader.__init__(self, config)
        self._objects_mapping = self.config.get_list("mapping")

    def run(self):
        # For each object to be loaded:
            # Add to the scene
            # Hide it from the renderer
            # Set the replacing custom property

        for map_ in self._objects_mapping:
            paths = map_['paths']
            # Replacing which category
            replacing = map_['category']
            for path in paths:
                file_path = Utility.resolve_path(path)
                loaded_objects = Utility.import_objects(filepath=file_path)
                if len(loaded_objects) > 0:
                    for obj in loaded_objects:
                        obj.hide_render = True
                        obj['ikea'] = 1
                        obj['replacing'] = replacing
                    self._set_physics_property(loaded_objects)
