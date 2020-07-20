import os
import glob
import warnings

import bpy

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility


class TextureLoader(LoaderInterface):
    """ Depending on the form of the provided path:
        1. Loads an image, creates an image texture, and assigns the loaded image to the texture, when a path to an
        image is provided.
        2. Loads images and for each creates a texture, and assing an image to this texture, if a path to a
        folder with images is provided.

        NOTE: Same image file can be loaded once to avoid unnecessary overhead. If you really need the same image in
        different colorspaces, then have a copy per desired colorspace and load them in different instances of this Loader.

        Example 1: Load all images in the folder in sRGB colorspace and create appropriate textures.

        {
          "module": "loader.TextureLoader",
          "config": {
            "path": "path/to/folder/with/assets/"
          }
        }

        Example 2: Load a random image from the path in Non-color colorscpace and create an appropriate texture.

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

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "The path to the folder with assets/to the asset. Type: string."
       "colorspace", "Colorspace type to assign to loaded assets. Type: string. Available: 'Filmic Log', 'Linear',
                     'Linear ACES', 'Non-Color', 'Raw', 'sRGB', 'XYZ'. Default: 'sRGB'."
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        """ Loads images and creates image textures. """
        path = Utility.resolve_path(self.config.get_string("path"))
        colorspace = self.config.get_string("colorspace", "sRGB")
        image_paths = self._resolve_paths(path)
        textures = self._load_and_create(image_paths, colorspace)

        self._set_properties(textures)

    @staticmethod
    def _resolve_paths(path):
        """ Resolves absolute paths to assets in the provided folder, or to an asset if an appropriate path is provided.

        :param path: Path to folder containing assets or path to an asset. Type: string.
        :return: List of absolute paths to assets. Type: list.
        """
        image_paths = []
        if os.path.exists(path):
            if os.path.isdir(path):
                image_paths = glob.glob(os.path.join(path, "*"))
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
        :return: Created textures. Type: list.
        """
        existing = [image.filepath for image in bpy.data.images]
        textures = []
        for image_path in image_paths:
            dir_path = os.path.dirname(image_path)
            file_name = os.path.basename(image_path)
            if image_path not in existing:
                bpy.ops.image.open(filepath=image_path, directory=dir_path)
                existing.append(image_path)
                # take the last loaded image (the very last is Render Result, so we take -2)
                loaded_image = bpy.data.images[-2]
                loaded_image.colorspace_settings.name = colorspace
                texture_name = "ct_{}".format(loaded_image.name)
                tex = bpy.data.textures.new(name=texture_name, type="IMAGE")
                tex.image = bpy.data.images.get(file_name)
                tex.use_nodes = True
                textures.append(tex)
            else:
                warnings.warn("Image {} has been already loaded and a corresponding texture was created. Following the "
                              "save behaviour of reducing the overhead, it is skipped. So, if you really need to load the "
                              "same image again (for example, in a different or in the same colorspace), use the copy "
                              "of the file.".format(image_path))

        return textures
