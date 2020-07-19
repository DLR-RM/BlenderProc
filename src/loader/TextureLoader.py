import os

import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class TextureLoader(Loader):
    """ Loads an image, creates an image texture, and assigns the loaded image to the texture, when a path to an image
        is provided. Loads images and for each creates a texture, and assing an image to this texture, if a path to a
        folder with images is provided.

        Example 1: Load all images in the folder in sRGB colorspace and create appropriate textures.

        {
          "module": "loader.TextureLoader",
          "config": {
            "path": "absolute/path/to/folder/with/assets/"
          }
        }

        Example 2: Load a random image from the path in Non-color colorscpace and create an appropriate texture.

        {
          "module": "loader.TextureLoader",
          "config": {
            "path": {
              "provider": "sampler.Path",
              "path": "path/to/folder/*.png"
            }
          },
          "colorspace": "Raw"
        }

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "The path to the folder with assets/to the asset. Type: string."
       "colorspace", "Colorspace type to assign to loaded assets. Type: string. Available: 'Filmic Log', 'Linear',
                     'Linear ACES', 'Non-Color', 'Raw', 'sRGB', 'XYZ'. Default: 'sRGB'."
    """

    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        """ Loads images and creates image textures. """
        path = Utility.resolve_path(self.config.get_string("path"))
        colorspace = self.config.get_string("colorspace", "sRGB")
        image_paths = self._resolve_paths(path)
        self._load_and_create(image_paths, colorspace)

    @staticmethod
    def _resolve_paths(path):
        """ Resolves absolute paths to assets in the provided folder, or to an asset if an appropriate path is provided.

        :param path: Path to folder containing assets or path to an asset. Type: string.
        :return: List of absolute paths to assets. Type: list.
        """
        image_paths = []
        if os.path.exists(path):
            if os.path.isdir(path):
                path_contents = os.listdir(path)
                for image in path_contents:
                    image_paths.append(os.path.join(path, image))
            else:
                image_paths.append(path)
        else:
            raise RuntimeError("Invalid path: {}".format(path))

        return image_paths

    @staticmethod
    def _load_and_create(image_paths, colorspace):
        """ Loads an image, creates an image texture and assigns an image to this texture per each provided path.

        :param image_paths: List of absolute paths to assets. Type: list.
        :param colorspace: Colorspace type of the assets. Type: string.
        """
        for image_path in image_paths:
            dir_path = os.path.dirname(image_path)
            file_name = os.path.basename(image_path)
            bpy.ops.image.open(filepath=image_path, directory=dir_path)
            bpy.data.images[file_name].colorspace_settings.name = colorspace
            texture_name = "ct_{}".format(os.path.splitext(file_name)[0])
            tex = bpy.data.textures.new(name=texture_name, type="IMAGE")
            bpy.data.textures[texture_name].image = bpy.data.images.get(file_name)
            tex.use_nodes = True
