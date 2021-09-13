import os

from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.utility.Utility import resolve_path, Utility, resolve_resource
from blenderproc.python.loader.IKEALoader import load_ikea


class IKEALoaderModule(LoaderInterface):
    """
    This class loads objects from the IKEA dataset.

    Objects can be selected randomly, based on object type, object style, or both.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_dir
          - The directory with all the IKEA models. Default: 'resources/IKEA'
          - string
        * - category
          - The category to use for example: 'bookcase'. This can also be a list of elements. Default: None.
            Available: ['bed', 'bookcase', 'chair', 'desk', 'sofa', 'table', 'wardrobe']
          - string/list
        * - style
          - The IKEA style to use for example: 'hemnes'. Default: None. See data_dir for other options.
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

        self._data_dir = resolve_path(self.config.get_string("data_dir", resolve_resource("IKEA")))

        if self.config.has_param("category"):
            self._obj_categories = self.config.get_raw_value("category", None)
        else:
            self._obj_categories = None

        self._obj_style = self.config.get_raw_value("style", None)

    def run(self):
        loaded_obj = load_ikea(data_dir=self._data_dir, obj_categories=self._obj_categories, obj_style=self._obj_style)
        self._set_properties(loaded_obj)


