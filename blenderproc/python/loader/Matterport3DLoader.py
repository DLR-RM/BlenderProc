""" Loader for the Matterport3D dataset. """

import random
from typing import Union, Tuple, Optional
from pathlib import Path

from blenderproc.python.loader.ObjectLoader import load_obj
from blenderproc.python.object.FaceSlicer import slice_faces_with_normals
from blenderproc.python.types.MeshObjectUtility import MeshObject


def load_matterport3d(data_folder: Union[Path, str], used_house_id: Optional[str] = None,
                      compare_floor_angle_in_degrees: float = 15.0) -> Tuple[MeshObject, MeshObject]:
    """
    Load a scene from the Matterport3D dataset.

    :param data_folder: Path to the downloaded Matterport3D dataset, please use `blenderproc download matterport`
    :param used_house_id: A possible used_house_id for example: "X7HyMhZNoso" or "Z6MFQCViBuw", if None is given a
                          random one is selected
    :param compare_floor_angle_in_degrees: The angle which is used to check if a face is pointing upwards, all faces
                                           pointing upwards are used to extract the floor object
    :return: The general scene and the floor object as a tuple of `MeshObject`
    """

    data_folder = Path(data_folder)
    if not data_folder.exists():
        raise FileNotFoundError("The Matterport3D data folder must exist!")

    all_object_files = list(data_folder.glob("**/*.obj"))

    # the aayBHfsNo7d id can not be read by blender and is therefore remove
    all_object_files = [object_file for object_file in all_object_files if "aayBHfsNo7d" not in str(object_file)]

    if used_house_id is not None:
        loaded_house_file = [object_file for object_file in all_object_files if used_house_id in str(object_file)]
        if not loaded_house_file:
            raise ValueError(f"The used house id: {used_house_id} does not appear in the downloaded .obj files!")
        if len(loaded_house_file) == 1:
            loaded_house_file = loaded_house_file[0]
        else:
            raise ValueError(f"The used house id: {used_house_id} does appear more than once in the downloaded "
                             f".obj files!")
    else:
        loaded_house_file = random.choice(all_object_files)

    loaded_obj = load_obj(str(loaded_house_file), forward_axis="Y")
    if len(loaded_obj) == 1:
        obj = loaded_obj[0]
    else:
        raise RuntimeError(f"At this point only one object should be loaded, not more or less: {len(loaded_obj)}")

    # replace all BSDF materials with background materials, to avoid that any light is cast on the objects
    for material in obj.get_materials():
        principled_bsdf = material.get_the_one_node_with_type("BsdfPrincipled")
        material.remove_node(principled_bsdf)

        textures = material.get_the_one_node_with_type("ShaderNodeTexImage")
        background_color_node = material.new_node("ShaderNodeBackground")

        material.link(textures.outputs["Color"], background_color_node.inputs["Color"])
        output_node = material.get_the_one_node_with_type("OutputMaterial")
        material.link(background_color_node.outputs["Background"], output_node.inputs["Surface"])

    # split away the floor object
    floor_obj = slice_faces_with_normals(obj, compare_angle_degrees=compare_floor_angle_in_degrees)

    return obj, floor_obj
