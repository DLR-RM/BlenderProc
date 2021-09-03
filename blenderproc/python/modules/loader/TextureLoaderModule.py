from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.loader.TextureLoader import load_texture


class TextureLoaderModule(LoaderInterface):
    """
    Depending on the form of the provided path:
    1. Loads an image, creates an image texture, and assigns the loaded image to the texture, when a path to an
    image is provided.
    2. Loads images and for each creates a texture, and assing an image to this texture, if a path to a
    folder with images is provided.

    NOTE: Same image file can be loaded once to avoid unnecessary overhead. If you really need the same image in
    different colorspaces, then have a copy per desired colorspace and load them in different instances of this Loader.

    Example 1: Load all images in the folder in sRGB colorspace and create appropriate textures.

    .. code-block:: yaml

        {
          "module": "loader.TextureLoader",
          "config": {
            "path": "path/to/folder/with/assets/"
          }
        }

    Example 2: Load a random image from the path in raw colorspace and create an appropriate texture.

    .. code-block:: yaml

        {
          "module": "loader.TextureLoader",
          "config": {
            "path": {
              "provider": "sampler.Path",
              "path": "path/to/folder/with/assets/*.png"
            }
          },
          "colorspace": "Raw"
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - path
          - The path to the folder with assets/to the asset.
          - string
        * - colorspace
          - Colorspace type to assign to loaded assets. Default: 'sRGB'. Available: ['Filmic Log', 'Linear', 'Linear
            ACES', 'Non-Color', 'Raw', 'sRGB', 'XYZ'].
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        """ Loads images and creates image textures. """
        textures = load_texture(self.config.get_string("path"), self.config.get_string("colorspace", "sRGB"))

        self._set_properties(textures)
