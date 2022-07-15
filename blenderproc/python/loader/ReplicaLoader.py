import os
from typing import List, Union
from pathlib import Path
import json

import numpy as np

from blenderproc.python.types.MeshObjectUtility import MeshObject, create_with_empty_mesh
from blenderproc.python.loader.ObjectLoader import load_obj


def load_replica_segmented_mesh(data_path: Union[str, Path], data_set_name: str, use_smooth_shading: bool = False) -> List[MeshObject]:
    """
    Loads a segmented replica file

    :param data_path: The path to the data folder, where all rooms are saved.
    :param data_set_name: Name of the room (for example: apartment_0).
    :param use_smooth_shading: if set to True all objects loaded, will have smooth shading activated
    :return: The list of loaded and separated mesh objects.
    """
    try:
        import plyfile
    except ModuleNotFoundError:
        raise Exception("This function needs the plyfile lib, install it via:\n\tblenderproc pip install plyfile")

    if isinstance(data_path, str):
        data_path = Path(data_path)

    current_folder = data_path / data_set_name

    if not current_folder.exists():
        raise Exception(f"The dataset folder: \"{current_folder}\" does not exist!")

    json_file_path = current_folder / "habitat" / "info_semantic.json"

    class_mapping = {}
    with open(json_file_path, "r") as file:
        data = json.load(file)

    for ele in data["classes"]:
        if "id" in ele:
            class_mapping[ele["id"]] = ele["name"]
    for ele in data["objects"]:
        if "id" in ele:
            class_mapping[ele["id"]] = ele["class_name"]

    ply_segmented_path = current_folder / "habitat" / "mesh_semantic.ply"
    if not ply_segmented_path.exists():
        raise Exception(f"Could not find \"{ply_segmented_path}\", the path was created automatically.")

    plydata = plyfile.PlyData.read(str(ply_segmented_path))

    vertex_data = np.array([e.tolist() for e in plydata["vertex"]])
    vertices = vertex_data[:, :3]
    normals = vertex_data[:, 3:6]
    # add alpha channel
    colors = np.concatenate([vertex_data[:, 6:].astype(float) / 255.0, np.ones((vertex_data.shape[0], 1))], axis=-1)

    # extract the face indices and the class ids
    face_indices = np.array([e.tolist()[0] for e in plydata["face"]])
    class_face_ids = np.array([e.tolist()[1] for e in plydata["face"]])
    used_class_ids = np.unique(class_face_ids)

    objs = []
    for current_class_id in used_class_ids:
        if current_class_id in class_mapping:
            used_obj_name = class_mapping[current_class_id]
        else:
            used_obj_name = "undefined"
        obj = create_with_empty_mesh(used_obj_name, used_obj_name + "_mesh")
        # add this new data to the mesh object
        mesh = obj.get_mesh()

        # first select all currently used faces, based on the object id
        current_face_indices = face_indices[class_face_ids == current_class_id]
        amount_of_vertices = current_face_indices.shape[1]
        current_face_indices = current_face_indices.reshape(-1)
        # as we add all vertices used for the current object, the face indices order is just from 0
        # to amount of vertices
        vertex_indices = np.arange(0, current_face_indices.shape[0])

        # add vertices
        mesh.vertices.add(current_face_indices.shape[0])
        mesh.vertices.foreach_set("co", vertices[current_face_indices].reshape(-1))
        mesh.vertices.foreach_set("normal", normals[current_face_indices].reshape(-1))

        # add faces
        num_vertex_indicies = len(vertex_indices)
        mesh.loops.add(num_vertex_indicies)
        mesh.loops.foreach_set("vertex_index", vertex_indices)

        # the loops are set based on how the faces are a ranged
        num_loops = int(num_vertex_indicies // amount_of_vertices)
        mesh.polygons.add(num_loops)
        # always amount_of_vertices vertices form one polygon
        loop_start = np.arange(0, num_vertex_indicies, amount_of_vertices)
        # the total size of each triangle is therefore amount_of_vertices
        loop_total = [amount_of_vertices] * num_loops
        mesh.polygons.foreach_set("loop_start", loop_start)
        mesh.polygons.foreach_set("loop_total", loop_total)

        # this update is needed else the vertex colors can't be set
        mesh.update()

        # check if the mesh already has some vertex colors
        if not mesh.vertex_colors:
            mesh.vertex_colors.new()
        # get the newly created vertex colors
        color_layer = mesh.vertex_colors["Col"]
        color_layer.data.foreach_set("color", colors[current_face_indices].reshape(-1))
        # one final update to integrate the vertex colors
        mesh.update()

        objs.append(obj)

    # add smoothing if requested
    if use_smooth_shading:
        for obj in objs:
            obj.set_shading_mode("SMOOTH")

    return objs


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