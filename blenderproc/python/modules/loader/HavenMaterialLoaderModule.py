from blenderproc.python.modules.main.Module import Module
from blenderproc.python.loader.HavenMaterialLoader import load_haven_mat


class HavenMaterialLoaderModule(Module):
    """
    This modules loads all textures obtained from https://texturehaven.com, use the script
    (scripts/download_haven.py) to download all the textures to your pc.

    All textures here support Physically based rendering (PBR), which makes the textures more realistic.

    There is a preload option, in which you only load empty materials, without any loaded textures, these are than
    later filled, when an object really uses them. This saves on loading times:

    .. code-block:: yaml

        {
          "module": "loader.HavenMaterialLoader",
          "config": {
            "folder_path": "<args:0>", # this would be resources/haven/textures
            "preload": True
          }
        }

    After you have used them maybe with an manipulators.EntityManipulator, you can load the ones you really assign to
    an object. By:

    .. code-block:: yaml

        {
          "module": "loader.HavenMaterialLoader",
          "config": {
            "folder_path": "<args:0>",
            "fill_used_empty_materials": True
          }
        }

    **Configuration**:

    .. list-table::
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - folder_path
          - The path to the downloaded haven. Default: resources/haven.
          - string
        * - used_assets
          - A list of all asset names, you want to use. The asset-name must not be typed in completely, only the
            beginning the name starts with. By default all assets will be loaded, specified by an empty list.
            Default: [].
          - list
        * - add_custom_properties
          - A dictionary of materials and the respective properties. Default: {}.
          - dict
        * - preload
          - If set true, only the material names are loaded and not the complete material. Default: False
          - bool
        * - fill_used_empty_materials
          - If set true, the preloaded materials, which are used are now loaded completely. Default: False
          - bool
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """
        Load the materials
        """

        load_haven_mat(
            folder_path=self.config.get_string("folder_path", "resources/haven"),
            used_assets=self.config.get_list("used_assets", []),
            add_cp=self.config.get_raw_dict("add_custom_properties", {}),
            preload=self.config.get_bool("preload", False),
            fill_used_empty_materials=self.config.get_bool("fill_used_empty_materials", False)
        )