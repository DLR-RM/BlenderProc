import os
from random import choice
import numpy as np
from typing import List, Union

import bpy
from mathutils import Vector

from blenderproc.python.types.MeshObjectUtility import MeshObject


class RockEssentialsRockLoader:
    """ Loads rocks/cliffs from a specified .blend Rocks Essentials file. """

    @staticmethod
    def load_rocks(path: str, subsec_num: int, objects: list = [], sample_objects: bool = False, amount: int = None) -> List[MeshObject]:
        """ Loads rocks from the given blend file.

        :param path: Path to a .blend file containing desired rock/cliff objects in //Object// section.
        :param subsec_num: Number of a corresponding cell (batch) in `rocks` list in configuration. Used for name generation.
        :param objects: List of rock-/cliff-object names to be loaded. If not specified then `amount` property is used for consequential loading.
        :param sample_objects: Toggles the uniform sampling of objects to load. Takes into account `objects` and `amount` parameters. Requires 'amount' param to be defined.
        :param amount: Amount of rock-/cliff-object to load. If not specified, the amount will be set to the amount of suitable
                       objects in the current section of a blend file. Must be bigger than 0.
        :return: List of loaded objects.
        """
        loaded_objects = []
        obj_types = ["Rock", "Cliff"]
        amount_defined = False

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
        if amount is not None:
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
            loaded_obj = MeshObject(bpy.context.scene.objects[obj])
            # set custom name for easier tracking in the scene
            loaded_obj.set_name(obj + "_" + str(subsec_num) + "_" + str(i))
            # append to return list
            loaded_objects.append(loaded_obj)

        return loaded_objects

    @staticmethod
    def set_rocks_properties(objects: List[MeshObject], physics: bool = False, render_levels: int = 3, high_detail_mode: bool = False, 
                             scale: Union[Vector, np.ndarray, list] = [1, 1, 1], reflection_amount: float = None, reflection_roughness: float = None, hsv: list = None):
        """ Sets rocks properties in accordance to the given parameters.

        :param objects: List of loaded rock mesh objects.
        :param physics: Custom property for physics/rigidbody state.
        :param render_levels: Number of subdivisions to perform when rendering.
        :param high_detail_mode: Flag for enabling HDM when possible.
        :param scale: Scale of a rock as a 3d-vector with each value as a scaling factor per according dimension.
        :param reflection_amount: Reflection texture value. Default: rock-specific. Range: [0,1]
        :param reflection_roughness: Roughness texture value. Default: rock-specific. Range: [0,1]
        :param hsv: Hue-Saturation-Value parameters of the HSV node. (3 values). Range: H: [0, 1], S: [0, 2], V: [0, 2]. Default: rock-specific.
        """

        for obj in objects:
            # set physics parameter
            obj.set_cp("physics", physics)
            # set category id
            obj.set_cp("category_id", 1)
            # set render value
            obj.blender_obj.modifiers["Subsurf"].render_levels = render_levels
            # set scale
            obj.set_scale(scale)
            # set HDM if enabled
            if obj.has_cp("01) High Detail Mode"):
                obj.set_cp("01) High Detail Mode", high_detail_mode)
            else:
                print("High Detail Mode is unavailable for " + str(obj.get_name()) + ", omitting.")
            if reflection_amount is not None:
                obj.set_cp("05) Reflection Amount", reflection_amount)
            if reflection_roughness is not None:
                obj.set_cp("06) Reflection Roughness", reflection_roughness)
            if hsv is not None:
                obj.set_cp("02) Saturation", hsv[1])
                obj.set_cp("03) Hue", hsv[0])
                obj.set_cp("04) Value", hsv[2])
