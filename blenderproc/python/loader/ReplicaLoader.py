import os
from typing import List

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.loader.ObjectLoader import load_obj

def load_replica(data_path: str, data_set_name: str, use_smooth_shading: bool = False) -> List[MeshObject]:
    """ Just imports the configured .ply file straight into blender for the replica case.

    :param data_path: The path to the data folder, where all rooms are saved.
    :param data_set_name: Name of the room (for example: apartment_0).
    :param use_smooth_shading: Enable smooth shading on all surfaces, instead of flat shading.
    :return: The list of loaded mesh objects.
    """
    file_path = os.path.join(data_path, data_set_name, 'mesh.ply')
    loaded_objects = load_obj(file_path)

    if use_smooth_shading:
        for obj in loaded_objects:
            obj.set_shading_mode("SMOOTH")

    return loaded_objects