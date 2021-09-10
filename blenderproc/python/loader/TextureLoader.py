import glob
import os
import warnings
from typing import List

import bpy

from blenderproc.python.utility.Utility import resolve_path

def load_texture(path: str, colorspace: str = "sRGB") -> List[bpy.types.Texture]:
    """ Loads images and creates image textures.

    Depending on the form of the provided path:
    1. Loads an image, creates an image texture, and assigns the loaded image to the texture, when a path to an
    image is provided.
    2. Loads images and for each creates a texture, and assing an image to this texture, if a path to a
    folder with images is provided.

    NOTE: Same image file can be loaded once to avoid unnecessary overhead. If you really need the same image in
    different colorspaces, then have a copy per desired colorspace and load them in different instances of this Loader.

    :param path: The path to the folder with assets/to the asset.
    :param colorspace: Colorspace type to assign to loaded assets. Available: ['Filmic Log', 'Linear', 'Linear ACES', 'Non-Color', 'Raw', 'sRGB', 'XYZ'].
    :return: The list of created textures.
    """
    path = resolve_path(path)
    image_paths = TextureLoader._resolve_paths(path)
    textures = TextureLoader._load_and_create(image_paths, colorspace)

    return textures


class TextureLoader:

    @staticmethod
    def _resolve_paths(path: str) -> list:
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
    def _load_and_create(image_paths: list, colorspace: str) -> List[bpy.types.Texture]:
        """ Loads an image, creates an image texture and assigns an image to this texture per each provided path.

        :param image_paths: List of absolute paths to assets. Type: list.
        :param colorspace: Colorspace type of the assets. Type: string.
        :return: Created textures. Type: list.
        """
        existing = [image.filepath for image in bpy.data.images]
        textures = []
        for image_path in image_paths:
            if image_path not in existing:
                loaded_image = bpy.data.images.load(filepath=image_path)
                existing.append(image_path)
                loaded_image.colorspace_settings.name = colorspace
                texture_name = "ct_{}".format(loaded_image.name)
                tex = bpy.data.textures.new(name=texture_name, type="IMAGE")
                tex.image = loaded_image
                tex.use_nodes = True
                tex.type = "IMAGE"
                textures.append(tex)
            else:
                warnings.warn("Image {} has been already loaded and a corresponding texture was created. Following the "
                              "save behaviour of reducing the overhead, it is skipped. So, if you really need to load the "
                              "same image again (for example, in a different or in the same colorspace), use the copy "
                              "of the file.".format(image_path))
        return textures