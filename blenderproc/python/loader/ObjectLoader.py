"""Provides `load_obj`, which allows to load different 3D object files. """

import os
import re
from typing import List, Optional, Dict

import bpy

from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes
from blenderproc.python.utility.Utility import Utility
from blenderproc.python.material.MaterialLoaderUtility import create_material_from_texture
from blenderproc.python.material.MaterialLoaderUtility import create as create_material


def load_obj(filepath: str, cached_objects: Optional[Dict[str, List[MeshObject]]] = None,
             use_legacy_obj_import: bool = False, **kwargs) -> List[MeshObject]:
    """ Import all objects for the given file and returns the loaded objects

    In .obj files a list of objects can be saved in.
    In .ply files only one object can be saved so the list has always at most one element

    :param filepath: the filepath to the location where the data is stored
    :param cached_objects: a dict of filepath to objects, which have been loaded before, to avoid reloading
                           (the dict is updated in this function)
    :param use_legacy_obj_import: If this is true the old legacy obj importer in python is used. It is slower, but
                                  it correctly imports the textures in the ShapeNet dataset.
    :param kwargs: all other params are handed directly to the bpy loading fct. check the corresponding documentation
    :return: The list of loaded mesh objects.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"The given filepath does not exist: {filepath}")

    if cached_objects is not None and isinstance(cached_objects, dict):
        if filepath in cached_objects.keys():
            created_obj = []
            for obj in cached_objects[filepath]:
                # duplicate the object
                created_obj.append(obj.duplicate())
            return created_obj
        loaded_objects = load_obj(filepath, cached_objects=None, **kwargs)
        cached_objects[filepath] = loaded_objects
        return loaded_objects
    # save all selected objects
    previously_selected_objects = bpy.context.selected_objects
    if filepath.endswith(".obj"):
        # load an .obj file:
        if use_legacy_obj_import:
            bpy.ops.import_scene.obj(filepath=filepath, **kwargs)
        else:
            bpy.ops.wm.obj_import(filepath=filepath, **kwargs)
    elif filepath.endswith(".ply"):
        PLY_TEXTURE_FILE_COMMENT = "comment TextureFile "
        model_name = os.path.basename(filepath)

        # Read file
        with open(filepath, "r", encoding="latin-1") as file:
            ply_file_content = file.read()

        # Check if texture file is given
        if PLY_TEXTURE_FILE_COMMENT in ply_file_content:
            # Find name of texture file
            texture_file_name = re.search(f"{PLY_TEXTURE_FILE_COMMENT}(.*)\n", ply_file_content).group(1)

            # Determine full texture file path
            texture_file_path = os.path.join(os.path.dirname(filepath), texture_file_name)
            material = create_material_from_texture(
                texture_file_path, material_name=f"ply_{model_name}_texture_model"
            )

            # Change content of ply file to work with blender ply importer
            new_ply_file_content = ply_file_content
            new_ply_file_content = new_ply_file_content.replace("property float texture_u", "property float s")
            new_ply_file_content = new_ply_file_content.replace("property float texture_v", "property float t")

            # Create temporary .ply file
            tmp_ply_file = os.path.join(Utility.get_temporary_directory(), model_name)
            with open(tmp_ply_file, "w", encoding="latin-1") as file:
                file.write(new_ply_file_content)

            # Load .ply mesh
            bpy.ops.import_mesh.ply(filepath=tmp_ply_file, **kwargs)

        else:  # If no texture was given
            # load a .ply mesh
            bpy.ops.import_mesh.ply(filepath=filepath, **kwargs)
            # Create default material
            material = create_material('ply_material')
            material.map_vertex_color()
        selected_objects = [obj for obj in bpy.context.selected_objects if obj not in previously_selected_objects]
        for obj in selected_objects:
            obj.data.materials.append(material.blender_obj)
    elif filepath.endswith('.dae'):
        bpy.ops.wm.collada_import(filepath=filepath)
    elif filepath.lower().endswith('.stl'):
        # load a .stl file
        bpy.ops.wm.stl_import(filepath=filepath, **kwargs)
        # add a default material to stl file
        mat = bpy.data.materials.new(name="stl_material")
        mat.use_nodes = True
        selected_objects = [obj for obj in bpy.context.selected_objects if
                                obj not in previously_selected_objects]
        for obj in selected_objects:
            obj.data.materials.append(mat)
    elif filepath.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif filepath.lower().endswith('.glb') or filepath.lower().endswith('.gltf'):
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif filepath.lower().endswith('.usda') or filepath.lower().endswith('.usd') or filepath.lower().endswith('.usdc'):
        bpy.ops.wm.usd_import(filepath=filepath)

    mesh_objects = convert_to_meshes([obj for obj in bpy.context.selected_objects
                                  if obj not in previously_selected_objects])
    # Add model_path cp to all objects
    for obj in mesh_objects:
        obj.set_cp("model_path", filepath)
    return mesh_objects
