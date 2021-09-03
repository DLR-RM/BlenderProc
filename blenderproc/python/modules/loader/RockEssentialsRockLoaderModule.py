from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.loader.RockEssentialsRockLoader import RockEssentialsRockLoader


class RockEssentialsRockLoaderModule(LoaderInterface):
    """
    Loads rocks/cliffs from a specified .blend Rocks Essentials file.

    Example 1: Load two rocks from the specified .blend file.

    .. code-block:: yaml

        {
          "module": "loader.RockEssentialsRockLoader",
          "config": {
            "batches": [
            {
              "path": "<args:0>/Rock Essentials/Individual Rocks/Sea/Rocks_Sea_Large.blend",
              "objects": ['Rock_Sea_Large001','Rock_Sea_Large003']
            }
            ]
          }
        }

    Example 2: Load 5 copies of two specified rocks from the specified .blend file.

    .. code-block:: yaml

        {
          "module": "loader.RockEssentialsRockLoader",
          "config": {
            "batches": [
            {
              "path": "<args:0>/Rock Essentials/Individual Rocks/Sea/Rocks_Sea_Large.blend",
              "objects": ['Rock_Sea_Large001','Rock_Sea_Large003'],
              "amount": 5
            }
            ]
          }
        }

    Example 3: Load 5 rocks, where each loaded rock is randomly selected out of a list of two rocks, from the specified
               .blend file.

    .. code-block:: yaml

        {
          "module": "loader.RockEssentialsRockLoader",
          "config": {
            "batches": [
            {
              "path": "<args:0>/Rock Essentials/Individual Rocks/Sea/Rocks_Sea_Large.blend",
              "objects": ['Rock_Sea_Large001','Rock_Sea_Large003'],
              "amount": 5,
              "sample_objects": True
            }
            ]
          }
        }

    Example 4: Load 5 random rocks from the specified .blend file.

    .. code-block:: yaml

        {
          "module": "loader.RockEssentialsRockLoader",
          "config": {
            "batches": [
            {
              "path": "<args:0>/Rock Essentials/Individual Rocks/Sea/Rocks_Sea_Large.blend",
              "amount": 5,
              "sample_objects": True
            }
            ]
          }
        }

    **configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - batches
          - Rocks to load. Each cell contains separate configuration data. Default: [].
          - list

    **Properties per rock batch**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - path
          - Path to a .blend file containing desired rock/cliff objects in //Object// section.
          - string
        * - objects
          - List of rock-/cliff-object names to be loaded. If not specified then `amount` property is used for
            consequential loading. Default: [].
          - list
        * - amount
          - Amount of rock-/cliff-object to load. If not specified, the amount will be set to the amount of suitable
            objects in the current section of a blend file. Must be bigger than 0.
          - int
        * - sample_objects
          - Toggles the uniform sampling of objects to load. Takes into account `objects` and `amount` parameters.
            Default: False. Requires 'amount' param to be defined.
          - bool
        * - render_levels
          - Number of subdivisions to perform when rendering. Default: 3.
          - int
        * - high_detail_mode
          - Flag for enabling HDM when possible. Default: False.
          - boolean
        * - reflection_amount
          - Reflection texture value. Default: rock-specific. Range: [0,1]
          - float
        * - reflection_roughness
          - Roughness texture value. Default: rock-specific. Range: [0,1]
          - float
        * - physics
          - Custom property for physics/rigidbody state. Default: False.
          - boolean
        * - scale
          - Scale of a rock as a 3d-vector with each value as a scaling factor per according dimension. Default: [1,
            1, 1].
          - mathutils.Vector
        * - HSV
          - Hue-Saturation-Value parameters of the HSV node. (3 values). Range: H: [0, 1], S: [0, 2], V: [0, 2].
            Default: rock-specific.
          - list
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        """ Loads rocks."""

        rocks_settings = self.config.get_list("batches", [])
        for subsec_num, subsec_settings in enumerate(rocks_settings):
            subsec_config = Config(subsec_settings)

            subsec_objects = RockEssentialsRockLoader.load_rocks(
                path=subsec_config.get_string("path"),
                subsec_num=subsec_num,
                objects=subsec_config.get_list("objects", []),
                sample_objects=subsec_config.get_bool("sample_objects", False),
                amount=subsec_config.get_int("amount", None)
            )

            RockEssentialsRockLoader.set_rocks_properties(
                objects=subsec_objects,
                physics=subsec_config.get_bool("physics", False),
                render_levels=subsec_config.get_int("render_levels", 3),
                high_detail_mode=subsec_config.get_bool("high_detail_mode", False),
                scale=subsec_config.get_vector3d("scale", [1, 1, 1]),
                reflection_amount=subsec_config.get_float("reflection_amount", None),
                reflection_roughness=subsec_config.get_float("reflection_roughness", None),
                hsv=subsec_config.get_list("HSV", None)
            )

