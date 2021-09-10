import random

from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.material import MaterialLoaderUtility


class Texture(Provider):
    """
    Uniformly samples a Texture for material manipulator.

    Example 1: Sample a random texture without exclusions:

    .. code-block:: yaml

        {
          "provider": "sampler.Texture",
        }

    Example 2: Sample a random texture within given textures:

    .. code-block:: yaml

        {
          "provider": "sampler.Texture",
          "textures": ["VORONOI", "MARBLE", "MAGIC"]
        }

    Example 3: Add parameters for texture Voronoi (Voroni is currently the only texture supported for doing this):

    .. code-block:: yaml

        {
          "provider": "sampler.Texture",
          "textures": ["VORONOI"],
          "noise_scale": 40,
          "noise_intensity": 1.1,
          "nabla": {
            "provider": "sampler.Value",
               "type": "float",
               "mode": "normal",
               "mean": 0.0,
               "std_dev": 0.05
          }
        }


    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - textures
          - A list of texture names. If not None the provider returns a uniform random sampled texture of one of
            those given texture names. Otherwise it returns a uniform random sampled texture of one of the available
            blender textures. Default: []. Available: ['CLOUDS', 'DISTORTED_NOISE'," 'MAGIC', 'MARBLE', 'MUSGRAVE',
            'NOISE', 'STUCCI', 'VORONOI', 'WOOD']
          - list
        * - noise_scale
          - Scaling for noise input. Default: 0.25. Only for VORONOI.
          - float
        * - noise_intensity
          - Scales the intensity of the noise. Default: 1.0. Only for VORONOI.
          - float
        * - nabla
          - Size of derivative offset used for calculating normal. Default: 0.03. Only for VORONOI.
          - float
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Samples a texture uniformly.

        :return: Texture. Type: bpy.types.Texture
        """
        # given textures
        given_textures = self.config.get_list("textures", [])

        if len(given_textures) > 0:
            texture_name = random.choice(given_textures).upper()
        else:
            texture_name = None

        tex = MaterialLoaderUtility.create_procedural_texture(texture_name)

        if texture_name == "VORONOI":
            #default values are the values blender uses as default for texture Voronoi
            tex.noise_scale = self.config.get_float("noise_scale", 0.25)
            tex.noise_intensity = self.config.get_float("noise_intensity", 1.0)
            tex.nabla = self.config.get_float("nabla", 0.03)

        return tex

