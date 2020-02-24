import bpy
import os

from src.loader.Loader import Loader
from src.utility.Config import Config


class RockEssentialsRockLoader(Loader):
    """
    **Properties per rock batch**:

    .. csv-table::
       :header: "Keyword", "Description"

       "path", "Path to a .blend file containing desired rock/cliff objects in //Object// section. Type: string."
       "objects", "List of rock-/cliff-object names to be loaded. Type: list. Optional. Default value: []. If not specified then `amount` property is used for consequential loading."
       "amount", "Amount of rock-/cliff-object to load. Type: int. Optional. Default value: 0. If not specified amount will be set to the amount of suitable objects in the current section of a blend file."
       "render_levels", "Number of subdivisions to perform when rendering. Type: int. Optional. Default value: 3."
       "high_detail_mode", "Flag for enabling HDM when possible. Type: boolean. Optional. Default value: False."
       "reflection_amount", "Reflection texture value. Type: float (min=0, max=1). Default value: rock-specific."
       "reflection_roughness". "Roughness texture value. Type: float (min=0, max=1). Default value: rock-specific."
       "physics", "Custom property for physics/rigidbody state. Type: boolean. Optional. Default value: False."
       "scale", "Scale of a rock as a 3d-vector with each value as a scaling factor per according dimension. Optional. Type: mathutils Vector. Default value: [1, 1, 1]."
       "HSV", "Hue-Saturation-Value parameters of the HSV node. Type: list (3 values). Range: H: [0, 1], S: [0, 2], V: [0, 2]. Optional. Default value: rock-specific."
    """

    def __init__(self, config):
        Loader.__init__(self, config)

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
        # get path to .blend file
        path = batch_config.get_string("path")
        # get list of obj names, empty if not defined
        objects = batch_config.get_list("objects", [])
        # get amount of rocks in this batch, 0 if not defined
        amount = batch_config.get_int("amount", 0)

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
        # if amount of rocks to be loaded is zero (default value) - set amount such that every rock is loaded once
        if amount == 0:
            amount = len(obj_list)

        for i in range(amount):
            # load rock
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
