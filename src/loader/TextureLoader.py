import os

import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class TextureLoader(Loader):
    """

    """

    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        """

        """
        path = Utility.resolve_path(self.config.get_string("path"))

        image_paths = self._resolve_paths(path)
        self._load_and_create(image_paths)

    @staticmethod
    def _resolve_paths(path):
        """

        :param path:
        :return:
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
    def _load_and_create(image_paths):
        """

        :return:
        """
        for image_path in image_paths:
            dir_path = os.path.dirname(image_path)
            file_name = os.path.basename(image_path)
            bpy.ops.image.open(filepath=image_path, directory=dir_path)
            texture_name = "ct_{}".format(os.path.splitext(file_name)[0])
            bpy.data.textures.new(name=texture_name, type="IMAGE")
            bpy.data.textures[texture_name].image = bpy.data.images.get(file_name)
