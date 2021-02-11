import os
from typing import List

import bpy

from src.utility.MeshUtility import Mesh
from src.utility.loader.ObjectLoader import ObjectLoader


class ReplicaLoader:

    @staticmethod
    def load(data_path: str, data_set_name: str, use_ambient_occlusion: bool = False, use_smooth_shading: bool = False) -> List[Mesh]:
        """ Just imports the configured .ply file straight into blender for the replica case.

        :param data_path: The path to the data folder, where all rooms are saved.
        :param data_set_name: Name of the room (for example: apartment_0).
        :param use_ambient_occlusion: Use ambient occlusion to lighten up the scene, if the RgbRenderer is used.
        :param use_smooth_shading: Enable smooth shading on all surfaces, instead of flat shading.
        :return: The list of loaded mesh objects.
        """
        file_path = os.path.join(data_path, data_set_name, 'mesh.ply')
        loaded_objects = ObjectLoader.load(file_path)

        # TODO: this should not be done in a loader
        if use_ambient_occlusion:
            bpy.context.scene.world.light_settings.use_ambient_occlusion = True  # turn AO on
            bpy.context.scene.world.light_settings.ao_factor = 0.9  # set it to 0.5

        if use_smooth_shading:
            for obj in loaded_objects:
                obj.set_shading_mode(True)

        return loaded_objects
