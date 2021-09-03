from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.loader.ShapeNetLoader import load_shapenet


class ShapeNetLoaderModule(LoaderInterface):
    """
    This loads an object from ShapeNet based on the given synset_id, which specifies the category of objects to use.

    From these objects one is randomly sampled and loaded.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    Finally it sets all objects to have a category_id corresponding to the void class, 
    so it wouldn't trigger an exception in the SegMapRenderer.

    Note: if this module is used with another loader that loads objects with semantic mapping, make sure the other module is loaded first in the config file.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_path
          - The path to the ShapeNetCore.v2 folder.
          - string
        * - used_synset_id
          - The synset id for example: '02691156', check the data_path folder for more ids. More information about synset id available here: http://wordnetweb.princeton.edu/perl/webwn3.0
          - string
        * - used_source_id
          - The identifier of the original model on the online repository from which it was collected to build the ShapeNet dataset.
          - string
        * - move_object_origin
          - Moves the object center to the bottom of the bounding box in Z direction and also in the middle of the X and Y plane, this does not change the `.location` of the object. Default: True
          - bool
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        """
        Uses the loaded .obj files and picks one randomly and loads it
        """
        loaded_obj = load_shapenet(
            data_path=self.config.get_string("data_path"),
            used_synset_id=self.config.get_string("used_synset_id"),
            used_source_id=self.config.get_string("used_source_id", ""),
            move_object_origin=self.config.get_bool("move_object_origin", True)
        )
        self._set_properties([loaded_obj])