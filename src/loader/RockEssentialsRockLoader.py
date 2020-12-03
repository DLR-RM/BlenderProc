import os
from random import choice

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Config import Config


class RockEssentialsRockLoader(LoaderInterface):
    """
    Loads rocks/cliffs from a specified .bled Rocks Essentials file.

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
          - Reflection texture value. Default: rock-specific.
          - float (min=0, max=1)
        * - reflection_roughness
          - Roughness texture value. Default: rock-specific.
          - float (min=0, max=1)
        * - physics
          - Custom property for physics/rigidbody state. Default: False.
          - boolean
        * - scale
          - Scale of a rock as a 3d-vector with each value as a scaling factor per according dimension. Default: [1,
            1, 1].
          - mathutils Vector
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
            subsec_objects = self._load_rocks(subsec_num, subsec_config)
            self._set_rocks_properties(subsec_objects, subsec_config)

    def _load_rocks(self, subsec_num, batch_config):
        """ Loads rocks.

        :param subsec_num: Number of a corresponding cell (batch) in `rocks` list in configuration. Used for name generation.
        :param batch_config: Config object that contains user-defined settings for a current batch.
        :return: List of loaded objects.
        """
        loaded_objects = []
        obj_types = ["Rock", "Cliff"]
        amount_defined = False
        # get path to .blend file
        path = batch_config.get_string("path")
        # get list of obj names, empty if not defined
        objects = batch_config.get_list("objects", [])
        # toggle object sampling
        sample_objects = batch_config.get_bool("sample_objects", False)

        obj_list = []
        with bpy.data.libraries.load(path) as (data_from, data_to):
            # if list of names is empty
            if not objects:
                # get list of rocks suitable for loading - objects that are rocks or cliffs
                for obj_type in obj_types:
                    obj_list += [obj for obj in data_from.objects if obj_type in obj]
            else:
                # if names are defined - get those that are available in this .blend file
                obj_list = [obj for obj in data_from.objects if obj in objects]

        # get amount of rocks in this batch, set to all suitable if not defined
        if batch_config.has_param("amount"):
            amount = batch_config.get_int("amount")
            amount_defined = True
            if amount == 0:
                raise RuntimeError("Amount param can't be equal to zero!")
        else:
            amount = len(obj_list)

        for i in range(amount):
            # load rock: choose random from the list if sampling is True, go through list if not
            if sample_objects and amount_defined:
                obj = choice(obj_list)
            else:
                obj = obj_list[i % len(obj_list)]
            bpy.ops.wm.append(filepath=os.path.join(path, "/Object", obj), filename=obj,
                              directory=os.path.join(path + "/Object"))
            loaded_obj = bpy.context.scene.objects[obj]
            # set custom name for easier tracking in the scene
            bpy.context.scene.objects[obj].name = obj + "_" + str(subsec_num) + "_" + str(i)
            # append to return list
            loaded_objects.append(loaded_obj)

        return loaded_objects

    def _set_rocks_properties(self, objects, batch_config):
        """ Sets rocks properties in accordance to user-defined values.

        :param objects: List of objects.
        :param batch_config: Config object that contains user-defined settings for a current batch.
        """
        # get physics custom setting, 'passive' if not defined
        physics = batch_config.get_bool("physics", False)
        # get render level for a batch, '3' if not defined
        render_levels = batch_config.get_int("render_levels", 3)
        # get HDM custom setting for a batch, 'disabled'\'False' if not defined
        high_detail_mode = batch_config.get_bool("high_detail_mode", False)
        # get scale, original scale of 1 along all dims if not defined
        scale = batch_config.get_vector3d("scale", [1, 1, 1])
        # get reflection amount and reflection roughness if defined
        if batch_config.has_param("reflection_amount"):
            reflection_amount = batch_config.get_float("reflection_amount")
        else:
            reflection_amount = None
        if batch_config.has_param("reflection_roughness"):
            reflection_roughness = batch_config.get_float("reflection_roughness")
        else:
            reflection_roughness = None
        if batch_config.has_param("HSV"):
            hsv = batch_config.get_list("HSV")
        else:
            hsv = None

        for obj in objects:
            # set physics parameter
            obj["physics"] = physics
            # set category id
            obj["category_id"] = 1
            # set render value
            obj.modifiers["Subsurf"].render_levels = render_levels
            # set scale
            obj.scale = scale
            # set HDM if enabled
            if "01) High Detail Mode" in obj:
                obj["01) High Detail Mode"] = high_detail_mode
            else:
                print("High Detail Mode is unavailable for " + str(obj.name) + ", omitting.")
            if reflection_amount is not None:
                obj["05) Reflection Amount"] = reflection_amount
            if reflection_roughness is not None:
                obj["06) Reflection Roughness"] = reflection_roughness
            if hsv is not None:
                obj["02) Saturation"] = hsv[1]
                obj["03) Hue"] = hsv[0]
                obj["04) Value"] = hsv[2]
