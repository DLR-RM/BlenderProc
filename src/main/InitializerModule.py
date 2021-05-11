from src.main.GlobalStorage import GlobalStorage
from src.main.Module import Module
from src.utility.Config import Config
from src.utility.Initializer import Initializer


class InitializerModule(Module):
    """ Does some basic initialization of the blender project.

     - Sets background color
     - Configures computing device
     - Creates camera
     - sets the device type to the fastest option possible -> OPTIX > CUDA > OPEN_CL

     If you want deterministic outputs use the environment variable: "BLENDER_PROC_RANDOM_SEED" and set it to
     the desired seed. (random and numpy random are effected by this)

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - horizon_color
          - A list of three elements specifying rgb of the world's horizon/background color. Default: [0.05, 0.05, 0.05].
          - list
        * - global
          - A dictionary of all global set attributes, which are used if a module does not provide a certain key.
            Default: {}.
          - dict
    """

    def __init__(self, config):
        Module.__init__(self, config)

        # Clean up example scene or scene created by last run when debugging pipeline inside blender
        Initializer.cleanup()

        # setting up the GlobalStorage
        global_config = Config(self.config.get_raw_dict("global", {}))
        GlobalStorage.init_global(global_config)

        # call the init again to make sure all values from the global config where read correctly, too
        self._default_init()

    def run(self):
        Initializer.init(self.config.get_list("horizon_color", [0.05, 0.05, 0.05]), clean_up_scene=False)