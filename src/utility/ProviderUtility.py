

from src.utility.EntityUtility import Entity
from src.utility.BlenderUtility import get_all_blender_mesh_objects
from src.utility.MeshObjectUtility import MeshObject


def get_all_mesh_objects():
    return MeshObject.convert_to_meshes(get_all_blender_mesh_objects())

def get_all_meshes_with_name(name: str):
    return MeshObject.convert_to_meshes([obj for obj in get_all_blender_mesh_objects() if obj.name == name])

