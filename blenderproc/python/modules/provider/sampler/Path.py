import random
from glob import glob
from random import choice

from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.utility.Utility import resolve_path


class Path(Provider):
    """
    Samples a path to one of the files in folder defined by a path.

    Example 1: return a path to a random .obj file in the defined folder.

    .. code-block:: yaml

        {
          "provider": "sampler.Path",
          "path": "/home/path/to/folder/*.obj"
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - path
          - A path to a folder containing files.
          - string
        * - random_samples
          - Amount of samples, which should be returned
          - int
        * - return_all
          - If this is true the full list is returned
          - bool
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Samples a path to an object.

        :return: A path to object. Type: string.
        """
        # get path to folder
        path = resolve_path(self.config.get_string("path"))

        # get list of paths
        paths = glob(path)

        if self.config.has_param("return_all"):
            return paths
        elif self.config.has_param("random_samples"):
            return random.choices(paths, k=self.config.get_int("random_samples"))
        else:
            # chose a random one
            chosen_path = choice(paths)

            return chosen_path
