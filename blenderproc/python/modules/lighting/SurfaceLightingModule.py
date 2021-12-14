from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes
from blenderproc.python.lighting.SurfaceLighting import light_surface


class SurfaceLightingModule(Module):
    """
    Adds lighting to the scene, by adding emission shader nodes to surfaces of specified objects.
    The speciality here is that the material can still look like before and now also emit light if emission_color is not set. 
    If the material should not be kept this can be set to `False` and
    with the key `emission_color` a new color can be set, if none is given it will assume `[1, 1, 1]`, which is white.

    **Configuration**:

    .. list-table::
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - selection
          - Selection of objects, via the `getter.Entity`.
          - Provider
        * - emission_strength
          - The strength of the emission shader. Default: 10.0.
          - float
        * - emission_color
          - If `keep_using_case_color` is False it is possible to set the color of the light with an RGB value. All \
            values have to be in the range from [0, 1]. Default: None.
          - mathutils.Vector
    """

    def __init__(self, config: Config):
        Module.__init__(self, config)
        self.emission_strength = self.config.get_float("emission_strength", 10.0)
        self.emission_color = self.config.get_vector4d("emission_color", None)

    def run(self):
        """
        Run this current module.
        """
        # get all objects which material should be changed
        objects = convert_to_meshes(self.config.get_list("selector"))

        light_surface(
            objects,
            emission_strength=self.emission_strength,
            emission_color=self.emission_color
        )
