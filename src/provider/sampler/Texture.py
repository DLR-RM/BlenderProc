import random

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


    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "textures", "A list of texture names. If not None the provider returns a uniform random sampled name of one"
                    "of those given texture names. Otherwise it returns a uniform random sampled name of one of the"
                    "possible blender textures (CLOUDS, DISTORTED_NOISE, MAGIC, MARBLE, MUSGRAVE, NOICE, STUCCI,
                    "VORONOI, WOOD). Type: list."
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
        given_textures = self.config.get_list("texture")

        if len(given_textures) == 0:
            return random.choice(possible_textures)
        else:
            return random.choice(given_textures).upper()

