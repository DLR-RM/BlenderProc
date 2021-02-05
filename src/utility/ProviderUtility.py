

from src.utility.EntityUtility import Entity
from src.utility.BlenderUtility import get_all_blender_mesh_objects



def get_all_mesh_objects():
    return Entity.convert_to_entities(get_all_blender_mesh_objects())

def get_all_meshes_with_name(name: str):
    return Entity.convert_to_entities([obj for obj in get_all_blender_mesh_objects() if obj.name == name])

