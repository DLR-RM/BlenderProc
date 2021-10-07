from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.loader.Pix3DLoader import load_pix3d


class Pix3DLoaderModule(LoaderInterface):
    """
    This loads an object from Pix3D based on the given category of objects to use.

    From these objects one is randomly sampled and loaded.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    Finally it sets all objects to have a category_id corresponding to the void class, 
    so it wouldn't trigger an exception in the SegMapRenderer.

    Note: if this module is used with another loader that loads objects with semantic mapping, make sure the other
    module is loaded first in the config file.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_path
          - The path to the Pix3D folder. Default: 'resources/pix3d'.
          - string
        * - category
          - The category to use for example: 'bed', check the data_path/model folder for more categories. Available:
            ['bed', 'bookcase', 'chair', 'desk', 'misc', 'sofa', 'table', 'tool'" , 'wardrobe']
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        loaded_obj = load_pix3d(self.config.get_string("used_category"), self.config.get_string("data_path", "resources/pix3d"))
        self._set_properties(loaded_obj)