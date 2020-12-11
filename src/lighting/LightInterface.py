import bpy

from src.main.Module import Module
from src.utility.ItemCollection import ItemCollection


class LightInterface(Module):
    """ 
    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cross_source_settings
          - See the next table for which properties can be set. Default: {}.
          - dict

    **Properties per lights entry**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - location
          - The position of the light source, specified as a list of three values. Default: [0, 0, 0]
          - list
        * - rotation
          - The rotation of the light source, specified as a list of three euler angles. Default: [0, 0, 0]
          - list
        * - color
          - Light color, specified as a list of three values [R, G, B]. Default: [1, 1, 1]. Range: [0, inf]
          - list
        * - distance
          - Falloff distance of the light = point where light is half the original intensity. Default: 0. Range: [0, inf]
          - float
        * - energy
          - Intensity of the emission of a light source. Default: 10.
          - float
        * - type
          - The type of a light source. Default: POINT. Available: [POINT, SUN, SPOT, AREA]
          - string
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.cross_source_settings = self.config.get_raw_dict("cross_source_settings", {})
        self.light_source_collection = ItemCollection(self._add_light_source, self.cross_source_settings)

    def _add_light_source(self, config):
        """ Adds a new light source according to the given configuration.

        :param config: A configuration object which contains all parameters relevant for the new light source.
        """
        # Create light data, link it to the new object
        light_data = bpy.data.lights.new(name="light", type="POINT")
        light_obj = bpy.data.objects.new(name="light", object_data=light_data)
        bpy.context.collection.objects.link(light_obj)

        light_data.type = config.get_string("type", 'POINT')
        light_obj.location = config.get_list("location", [0, 0, 0])
        light_obj.rotation_euler = config.get_list("rotation", [0, 0, 0])
        light_data.energy = config.get_float("energy", 10.)
        light_data.color = config.get_list("color", [1, 1, 1])[:3]
        light_data.distance = config.get_float("distance", 0)
