import bpy

from src.utility.Utility import Utility
from src.main.Module import Module


class WorldManipulator(Module):
    """ Allows basic manipulation of the blender world. Specify any desired {key: value} pairs.
    Each pair is treated like a {attribute_name:attribute_value} where attr_name is a custom property or a name of a
     custom property to create, while the attr_value is its new value.


    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "custom_property_name": "Value that custom_property should be set to."
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        world = bpy.context.scene.world
        for key in self.config.data.keys():

            requested_cp = False
            requested_cn = False

            if key.startswith('cp_'):
                requested_cp = True
                key = key[3:]
            elif key.startswith('cn_'):
                requested_cn = True
                key = key[3:]

            if hasattr(world, key) and all([not requested_cp, not requested_cn]):
                setattr(world, key, self.config.get_raw_value(key))
            elif requested_cp:
                world[key] = self.config.get_raw_value(key)
            elif requested_cn:
                if key == "bg_surface_color":
                    self._set_bg_surface_color(world, self.config.get_raw_value(key))
                elif key == "bg_surface_strength":
                    self._set_bg_surface_strength(world, self.config.get_raw_value(key))
                elif key == "bg_volume_color":
                    if not self._bg_volume_is_enabled(world):
                        self._enable_bg_volume(world)
                    self._set_bg_volume_color(world, self.config.get_raw_value(key))
                elif key == "bg_volume_strength":
                    if not self._bg_volume_is_enabled(world):
                        self._enable_bg_volume(world)
                    self._set_bg_volume_strength(world, self.config.get_raw_value(key))
                else:
                    raise RuntimeError('Unknown cn_ parameter: ' + key)
            else:
                raise RuntimeError('Unknown parameter: ' + key)

    def _set_bg_surface_color(self, world, color):
        """

        :param world:
        :param color:
        """
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[0].default_value = color

    def _set_bg_surface_strength(self, world, strength):
        """

        :param world:
        :param strength:
        """
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[1].default_value = strength

    def _set_bg_volume_color(self, world, color):
        """

        :param world:
        :param color:
        """
        world.node_tree.nodes["Background.001"].inputs[1].default_value = color

    def _set_bg_volume_strength(self, world, strength):
        """

        :param world:
        :param strength:
        """
        world.node_tree.nodes["Background.001"].inputs[1].default_value = strength

    def _bg_volume_is_enabled(self, world):
        """

        :param world:
        :return:
        """
        if len(Utility.get_nodes_with_type(world, "ShaderNodeBackground")) > 1:
            is_enabled = True
        else:
            is_enabled = False

        return is_enabled


    def _enable_bg_volume(self, world):
        """

        :param world:
        """
        world.use_nodes = True
        nodes = bpy.context.scene.world.node_tree.nodes
        links = bpy.context.scene.world.node_tree.links
        nodes.new("ShaderNodeBackground")
        node_output = nodes['Background.001'].outputs['Background']
        node_input = nodes['World Output'].inputs['Volume']
        links.new(node_output, node_input)
