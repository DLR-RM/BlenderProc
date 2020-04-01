import bpy

from src.main.Module import Module


class WorldManipulator(Module):
    """ Allows manipulation of the current World in the scene via specifying one or more {attr name/custom prop. name/
        custom name: value} pairs.

        Example 1: Sets the World's custom property `category_id` to 123

        {
          "module": "manipulators.WorldManipulator",
          "config": {
            "cp_category_id": 123
          }
        }

        Example 2: Sets the color and the strength of the light emitted by the background surface.

        {
          "module": "manipulators.WorldManipulator",
          "config": {
            "cn_bg_surface_color": [1, 1, 1, 1],
            "cn_bg_surface_strength": 100
          }
        }

        Example 3: Disables shader node tree of the background surface and sets a solid color to the background surface

        {
          "module": "manipulators.WorldManipulator",
          "config": {
            "use_nodes": False,
            "color": [0.5, 0.5, 0.5]
          }
        }

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "key": "Name of the attribute/custom prop. to change as a key in {name of an attr: value to set}. Type: string."
               "In order to specify, what exactly one want to modify (e.g. attribute, custom property, etc.):"
               "For attribute: key of the pair must be a valid attribute name of the world."
               "For custom property: key of the pair must start with `cp_` prefix."
               "For calling custom method: key of the pair must start with `cn_` prefix. See table below for supported"
               "cn names."
        "value": "Value of the attribute/custom prop. to set as a value in {name of an attr: value to set}."

    **Custom names**:

    .. csv-table::
        :header: "Parameter", "Description"

        "bg_surface_color", "Sets the color of the light emitted by the background. Input value type: list of RGBA values."
        "bg_surface_strength", "Sets the strength of the light emitted by the background. Input value type: float."
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        world = bpy.context.scene.world
        for key in self.config.data.keys():
            requested_cp = False
            requested_cn = False

            value = self.config.get_raw_value(key)

            if key.startswith('cp_'):
                requested_cp = True
                key = key[3:]
            elif key.startswith('cn_'):
                requested_cn = True
                key = key[3:]
            if hasattr(world, key) and all([not requested_cp, not requested_cn]):
                setattr(world, key, value)
            elif requested_cp:
                world[key] = value
            elif requested_cn:

                if key == "bg_surface_color":
                    self._set_bg_surface_color(world, value)
                elif key == "bg_surface_strength":
                    self._set_bg_surface_strength(world, value)
                else:
                    raise RuntimeError('Unknown cn_ parameter: ' + key)

            else:
                raise RuntimeError('Unknown parameter: ' + key)

    def _set_bg_surface_color(self, world, color):
        """ Sets the color of the emitted light by the background surface.

        :param world: World to modify. Type: World.
        :param color: Color of the emitted light. Type: RGBA vector.
        """
        world.node_tree.nodes["Background"].inputs['Color'].default_value = color

    def _set_bg_surface_strength(self, world, strength):
        """ Sets the strength of the emitted light by the background surface.

        :param world: World to modify. Type: World.
        :param strength: Strength of the emitted light. Type: float.
        """
        world.node_tree.nodes["Background"].inputs['Strength'].default_value = strength
