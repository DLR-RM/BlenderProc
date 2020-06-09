import random

import bpy
from src.main.Provider import Provider


class Texture(Provider):
    """ Uniformly samples a Texture for material manipulator.

        Example 1: Sample a random texture without exclusions:

        {
          "provider": "sampler.Texture",
        }

        Example 2: Sample a random texture within given textures:

        {
          "provider": "sampler.Texture",
          "textures": ["VORONOI", "MARBLE", "MAGIC"]
        }

        Example 3: Add parameters for texture Voronoi (Voroni is currently the only texture supported for doing this):

        {
          "provider": "sampler.Texture",
          "textures": ["VORONOI"]
          "noise_scale": 40
          "noise_intensity": 1.1
          "nabla": {
            "provider": "sampler.Value",
               "type": "dist",
               "mean": 0.0,
               "std_dev": 0.05
        }


    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "textures", "A list of texture names. If not None the provider returns a uniform random sampled name of one"
                    "of those given texture names. Otherwise it returns a uniform random sampled name of one of the"
                    "possible blender textures (CLOUDS, DISTORTED_NOISE, MAGIC, MARBLE, MUSGRAVE, NOICE, STUCCI,
                    "VORONOI, WOOD). Type: list."
        "noise_scale", "Texture-Parameter. Type: float. At the moment only texture VORONOI is supported."
        "noise_intensity", "Texture-Parameter. Type: float. At the moment only texture VORONOI is supported."
        "nabla", "Texture-Parameter. Type: float. At the moment only texture VORONOI is supported."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Samples a texture uniformly.

        :return: texture name. Type: string
        """

        possible_textures = ["CLOUDS", "DISTORTED_NOISE", "MAGIC", "MARBLE", "MUSGRAVE", "NOICE", "STUCCI",
                             "VORONOI", "WOOD"]

        # given textures
        given_textures = self.config.get_list("textures", [])

        if len(given_textures) == 0:
            texture_name = random.choice(possible_textures)
        else:
            texture_name = random.choice(given_textures).upper()

        tex = bpy.data.textures.new("ct_{}".format(texture_name), texture_name)

        if texture_name == "VORONOI":
            #default values are the values blender uses as default for texture Voronoi
            tex.noise_scale = self.config.get_float("noise_scale", 0.25)
            tex.noise_intensity = self.config.get_float("noise_intensity", 1.0)
            tex.nabla = self.config.get_float("nabla", 0.03)

        return tex

