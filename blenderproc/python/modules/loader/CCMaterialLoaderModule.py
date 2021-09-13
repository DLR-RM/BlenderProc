import os

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.utility.Utility import resolve_path, Utility, resolve_resource
from blenderproc.python.loader.CCMaterialLoader import load_ccmaterials


class CCMaterialLoaderModule(Module):
    """
    This modules loads all textures obtained from https://cc0textures.com, use the script
    (scripts/download_cc_textures.py) to download all the textures to your pc.

    All textures here support Physically based rendering (PBR), which makes the textures more realistic.

    All materials will have the custom property "is_cc_texture": True, which will make the selection later on easier.

    See the example section on how to use this in combination with a dataset: examples/datasets/shapenet_with_cctextures.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - folder_path
          - The path to the downloaded cc0textures. Default: resources/cctextures.
          - string
        * - used_assets
          - A list of all asset names, you want to use. The asset-name must not be typed in completely, only the
            beginning the name starts with. By default all assets will be loaded, specified by an empty list.
            Default: [].
          - list
        * - use_all_materials
          - If this is true all materials, which are available are used. This includes materials, which are not
            tileable an materials which have an alpha channel. By default only a reasonable selection is used.
            Default: False
          - bool
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
        if self.config.get_bool("use_all_materials", False) and self.config.has_param("used_assets"):
            raise Exception("It is impossible to use all materials and selected a certain list of assets!")

        load_ccmaterials(
            folder_path=resolve_path(self.config.get_string("folder_path", resolve_resource("cctextures"))),
            used_assets=self.config.get_list("used_assets", []),
            preload=self.config.get_bool("preload", False),
            fill_used_empty_materials=self.config.get_bool("fill_used_empty_materials", False),
            add_custom_properties=self.config.get_raw_dict("add_custom_properties", {}),
            use_all_materials=self.config.get_bool("use_all_materials", False)
        )
