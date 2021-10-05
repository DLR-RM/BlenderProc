import os
from typing import List, Optional, Dict

import bpy

from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes


def load_obj(filepath: str, cached_objects: Optional[Dict[str, List[MeshObject]]] = None, **kwargs) -> List[MeshObject]:
    """ Import all objects for the given file and returns the loaded objects

    In .obj files a list of objects can be saved in.
    In .ply files only one object can saved so the list has always at most one element

    :param filepath: the filepath to the location where the data is stored
    :param cached_objects: a dict of filepath to objects, which have been loaded before, to avoid reloading (the dict is updated in this function)
    :param kwargs: all other params are handed directly to the bpy loading fct. check the corresponding documentation
    :return: The list of loaded mesh objects.
    """
    if os.path.exists(filepath):
        if cached_objects is not None and isinstance(cached_objects, dict):
            if filepath in cached_objects.keys():
                created_obj = []
                for obj in cached_objects[filepath]:
                    # duplicate the object
                    created_obj.append(obj.duplicate())
                return created_obj
            else:
                loaded_objects = load_obj(filepath, cached_objects=None, **kwargs)
                cached_objects[filepath] = loaded_objects
                return loaded_objects
        else:
            # save all selected objects
            previously_selected_objects = bpy.context.selected_objects
            if filepath.endswith('.obj'):
                # load an .obj file:
                bpy.ops.import_scene.obj(filepath=filepath, **kwargs)
            elif filepath.endswith('.ply'):
                # load a .ply mesh
                bpy.ops.import_mesh.ply(filepath=filepath, **kwargs)
                # add a default material to ply file
                mat = bpy.data.materials.new(name="ply_material")
                mat.use_nodes = True
                selected_objects = [obj for obj in bpy.context.selected_objects if obj not in previously_selected_objects]
                for obj in selected_objects:
                    obj.data.materials.append(mat)

            return convert_to_meshes(
                [obj for obj in bpy.context.selected_objects if obj not in previously_selected_objects])
    else:
        raise Exception("The given filepath does not exist: {}".format(filepath))
