import os

from src.loader.LoaderInterface import LoaderInterface
from src.utility.loader.HavenEnvironmentLoader import HavenEnvironmentLoader


class HavenEnvironmentLoaderModule(LoaderInterface):
    """
    This module can load hdr images as background images, which will replace the default grey background.

    **Configuration**:

    .. list-table::
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_path
          - Path to the data folder, if this was downloaded via the script without changing the output folder, \
            then it is not necessary to add this value. Default: "resources/haven".
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        HavenEnvironmentLoader.set_random_world_background_hdr_img(
            self.config.get_string("data_path", os.path.join("resources", "haven"))
        )