"""Provides functions to load the objects inside the bop dataset."""

import os
from random import choice
from typing import List, Optional, Tuple
import warnings

import bpy
import numpy as np
from mathutils import Matrix, Vector

from blenderproc.python.utility.SetupUtility import SetupUtility
from blenderproc.python.camera import CameraUtility
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.utility.MathUtility import change_source_coordinate_frame_of_transformation_matrix
from blenderproc.python.loader.ObjectLoader import load_obj

def load_bop_objs(bop_dataset_path: str, model_type: str = "", obj_ids: Optional[List[int]] = None,
                  sample_objects: bool = False, num_of_objs_to_sample: Optional[int] = None,
                  obj_instances_limit: int = -1, mm2m: Optional[bool] = None, object_model_unit: str = 'm',
                  move_origin_to_x_y_plane: bool = False) -> List[MeshObject]:
    """ Loads all or a subset of 3D models of any BOP dataset

    :param bop_dataset_path: Full path to a specific bop dataset e.g. /home/user/bop/tless.
    :param model_type: Optionally, specify type of BOP model. Available: [reconst, cad or eval].
    :param obj_ids: List of object ids to load. Default: [] (load all objects from the given BOP dataset)
    :param sample_objects: Toggles object sampling from the specified dataset.
    :param num_of_objs_to_sample: Amount of objects to sample from the specified dataset. If this amount is bigger
                                  than the dataset actually contains, then all objects will be loaded.
    :param obj_instances_limit: Limits the amount of object copies when sampling. Default: -1 (no limit).
    :param mm2m: Specify whether to convert poses and models to meters (deprecated).
    :param object_model_unit: The unit the object model is in. Object model will be scaled to meters. This does not
                              affect the annotation units. Available: ['m', 'dm', 'cm', 'mm'].
    :param move_origin_to_x_y_plane: Move center of the object to the lower side of the object, this will not work
                                     when used in combination with pose estimation tasks! This is designed for the
                                     use-case where BOP objects are used as filler objects in the background.
    :return: The list of loaded mesh objects.
    """

    bop_path, bop_dataset_name = _BopLoader.setup_bop_toolkit(bop_dataset_path)

    # This import is done inside to avoid having the requirement that BlenderProc depends on the bop_toolkit
    # pylint: disable=import-outside-toplevel
    from bop_toolkit_lib import dataset_params

    # pylint: enable=import-outside-toplevel

    model_p = dataset_params.get_model_params(bop_path, bop_dataset_name, model_type=model_type if model_type else None)

    assert object_model_unit in ['m', 'dm', 'cm', 'mm'], (f"Invalid object model unit: `{object_model_unit}`. "
                                                          f"Supported are 'm', 'dm', 'cm', 'mm'")
    scale = {'m': 1., 'dm': 0.1, 'cm': 0.01, 'mm': 0.001}[object_model_unit]
    if mm2m is not None:
        warnings.warn("WARNING: `mm2m` is deprecated, please use `object_model_unit='mm'` instead!")
        scale = 0.001

    if obj_ids is None:
        obj_ids = []

    obj_ids = obj_ids if obj_ids else model_p['obj_ids']

    loaded_objects = []
    # if sampling is enabled
    if sample_objects:
        loaded_ids = {}
        loaded_amount = 0
        if obj_instances_limit != -1 and len(obj_ids) * obj_instances_limit < num_of_objs_to_sample:
            raise RuntimeError(f"{bop_dataset_path}'s contains {len(obj_ids)} objects, {num_of_objs_to_sample} object "
                               f"where requested to sample with an instances limit of {obj_instances_limit}. Raise "
                               f"the limit amount or decrease the requested amount of objects.")
        while loaded_amount != num_of_objs_to_sample:
            random_id = choice(obj_ids)
            if random_id not in loaded_ids:
                loaded_ids.update({random_id: 0})
            # if there is no limit or if there is one, but it is not reached for this particular object
            if obj_instances_limit == -1 or loaded_ids[random_id] < obj_instances_limit:
                cur_obj = _BopLoader.load_mesh(random_id, model_p, bop_dataset_name, scale)
                loaded_ids[random_id] += 1
                loaded_amount += 1
                loaded_objects.append(cur_obj)
            else:
                print(f"ID {random_id} was loaded {loaded_ids[random_id]} times with limit of {obj_instances_limit}. "
                      f"Total loaded amount {loaded_amount} while {num_of_objs_to_sample} are being requested")
    else:
        for obj_id in obj_ids:
            cur_obj = _BopLoader.load_mesh(obj_id, model_p, bop_dataset_name, scale)
            loaded_objects.append(cur_obj)
    # move the origin of the object to the world origin and on top of the X-Y plane
    # makes it easier to place them later on, this does not change the `.location`
    # This is only useful if the BOP objects are not used in a pose estimation scenario.
    if move_origin_to_x_y_plane:
        for obj in loaded_objects:
            obj.move_origin_to_bottom_mean_point()

    return loaded_objects


def load_bop_scene(bop_dataset_path: str, scene_id: int, model_type: str = "", cam_type: str = "",
                   split: str = "test", source_frame: Optional[List[str]] = None,
                   mm2m: Optional[bool] = None, object_model_unit: str = 'm') -> List[MeshObject]:
    """ Replicate a BOP scene from the given dataset: load scene objects, object poses, camera intrinsics and
        extrinsics

    - Interfaces with the bob_toolkit, allows loading of train, val and test splits
    - Relative camera poses are loaded/computed with respect to a reference model
    - Sets real camera intrinsics

    :param bop_dataset_path: Full path to a specific bop dataset e.g. /home/user/bop/tless.
    :param scene_id: Specify BOP dataset scene to synthetically replicate. Default: -1 (no scene is replicated,
                     only BOP Objects are loaded).
    :param model_type: Optionally, specify type of BOP model.  Available: [reconst, cad or eval].
    :param cam_type: Camera type. If not defined, dataset-specific default camera type is used.
    :param split: Optionally, test or val split depending on BOP dataset.
    :param source_frame: Can be used if the given positions and rotations are specified in frames different from the
                         blender frame. Has to be a list of three strings. Example: ['X', '-Z', 'Y']:
                         Point (1,2,3) will be transformed to (1, -3, 2). Default: ["X", "-Y", "-Z"],
                         Available: ['X', 'Y', 'Z', '-X', '-Y', '-Z'].
    :param mm2m: Specify whether to convert poses and models to meters (deprecated).
    :param object_model_unit: The unit the object model is in. Object model will be scaled to meters. This does not
                              affect the annotation units. Available: ['m', 'dm', 'cm', 'mm'].
    :return: The list of loaded mesh objects.
    """

    bop_path, bop_dataset_name = _BopLoader.setup_bop_toolkit(bop_dataset_path)

    # This import is done inside to avoid having the requirement that BlenderProc depends on the bop_toolkit
    # pylint: disable=import-outside-toplevel
    from bop_toolkit_lib import dataset_params, inout

    # pylint: enable=import-outside-toplevel

    if source_frame is None:
        source_frame = ["X", "-Y", "-Z"]

    model_p = dataset_params.get_model_params(bop_path, bop_dataset_name, model_type=model_type if model_type else None)
    try:
        split_p = dataset_params.get_split_params(bop_path, bop_dataset_name, split=split,
                                                  split_type=cam_type if cam_type else None)
    except ValueError as e:
        raise RuntimeError(f"Wrong path or {split} split does not exist in {bop_dataset_path}.") from e
    sc_gt = inout.load_scene_gt(split_p['scene_gt_tpath'].format(**{'scene_id': scene_id}))
    sc_camera = inout.load_json(split_p['scene_camera_tpath'].format(**{'scene_id': scene_id}))

    assert object_model_unit in ['m', 'dm', 'cm', 'mm'], (f"Invalid object model unit: `{object_model_unit}`. "
                                                          f"Supported are 'm', 'dm', 'cm', 'mm'")
    scale = {'m': 1., 'dm': 0.1, 'cm': 0.01, 'mm': 0.001}[object_model_unit]
    if mm2m is not None:
        warnings.warn("WARNING: `mm2m` is deprecated, please use `object_model_unit='mm'` instead!")
        scale = 0.001

    for i, (cam_id, insts) in enumerate(sc_gt.items()):
        cam_K, cam_H_m2c_ref = _BopLoader.get_ref_cam_extrinsics_intrinsics(sc_camera, cam_id, insts, scale)

        if i == 0:
            # define world = first camera
            cam_H_m2w_ref = cam_H_m2c_ref.copy()

            cur_objs = []
            # load scene objects and set their poses
            for inst in insts:
                cur_objs.append(_BopLoader.load_mesh(inst['obj_id'], model_p, bop_dataset_name, scale))
                _BopLoader.set_object_pose(cur_objs[-1], inst, scale)

        cam_H_c2w = _BopLoader.compute_camera_to_world_trafo(cam_H_m2w_ref, cam_H_m2c_ref, source_frame)
        # set camera intrinsics
        CameraUtility.set_intrinsics_from_K_matrix(cam_K, split_p['im_size'][0], split_p['im_size'][1])

        # set camera extrinsics as next frame
        frame_id = CameraUtility.add_camera_pose(cam_H_c2w)

        # Add key frame for camera shift, as it changes from frame to frame in the tless replication
        cam = bpy.context.scene.camera.data
        cam.keyframe_insert(data_path='shift_x', frame=frame_id)
        cam.keyframe_insert(data_path='shift_y', frame=frame_id)

        # Copy object poses to key frame (to be sure)
        for cur_obj in cur_objs:
            _BopLoader.insert_key_frames(cur_obj, frame_id)

    return cur_objs


def load_bop_intrinsics(bop_dataset_path: str, split: str = "test", cam_type: str = "") -> Tuple[np.ndarray, int, int]:
    """
    Load and set the camera matrix and image resolution of a specified BOP dataset

    :param bop_dataset_path: Full path to a specific bop dataset e.g. /home/user/bop/tless.
    :param split: Optionally, train, test or val split depending on BOP dataset, defaults to "test"
    :param cam_type: Camera type. If not defined, dataset-specific default camera type is used.
    :returns: camera matrix K, W, H
    """

    bop_path, bop_dataset_name = _BopLoader.setup_bop_toolkit(bop_dataset_path)

    # This import is done inside to avoid having the requirement that BlenderProc depends on the bop_toolkit
    # pylint: disable=import-outside-toplevel
    from bop_toolkit_lib import dataset_params

    # pylint: enable=import-outside-toplevel

    cam_p = dataset_params.get_camera_params(bop_path, bop_dataset_name, cam_type=cam_type if cam_type else None)

    try:
        split_p = dataset_params.get_split_params(bop_path, bop_dataset_name, split=split,
                                                  split_type=cam_type if cam_type else None)
    except ValueError as e:
        raise RuntimeError(f"Wrong path or {split} split does not exist in {bop_dataset_path}.") from e

    # TLESS exception because images are cropped
    if bop_dataset_name in ['tless']:
        cam_p['K'][0, 2] = split_p['im_size'][0] / 2
        cam_p['K'][1, 2] = split_p['im_size'][1] / 2

    # set camera intrinsics
    CameraUtility.set_intrinsics_from_K_matrix(cam_p['K'], split_p['im_size'][0], split_p['im_size'][1])

    return cam_p['K'], split_p['im_size'][0], split_p['im_size'][1]


class _BopLoader:
    CACHED_OBJECTS = {}
    @staticmethod
    def setup_bop_toolkit(bop_dataset_path: str) -> Tuple[str, str]:
        """
        Install the bop_toolkit from Github and set an environment variable pointing to the BOP datasets

        :param bop_dataset_path: Path to the bop dataset
        :return (bop_path, bop_dataset_name): Path to BOP datasets and BOP dataset name
        """

        bop_dataset_name = os.path.basename(bop_dataset_path)
        bop_path = os.path.dirname(bop_dataset_path)

        print(f"bob: {bop_dataset_path}, dataset_path: {bop_path}")
        print(f"dataset: {bop_dataset_name}")

        if not os.path.exists(bop_path):
            raise FileNotFoundError(f"It seems the BOP dataset does not exist under the given path {bop_dataset_path}")

        # Install bop_toolkit_lib
        SetupUtility.setup_pip(["git+https://github.com/thodan/bop_toolkit"])
        os.environ["BOP_PATH"] = bop_path

        return bop_path, bop_dataset_name

    @staticmethod
    def compute_camera_to_world_trafo(cam_H_m2w_ref: np.array, cam_H_m2c_ref: np.array,
                                      source_frame: List[str]) -> np.ndarray:
        """ Returns camera to world transformation in blender coords.

        :param cam_H_m2c_ref: (4x4) Homog trafo from object to camera coords.
        :param cam_H_m2w_ref: (4x4) Homog trafo from object to world coords.
        :param source_frame: Can be used if the given positions and rotations are specified in frames different
                             from the blender frame.
        :return: cam_H_c2w: (4x4) Homog trafo from camera to world coords.
        """

        cam_H_c2w = np.dot(cam_H_m2w_ref, np.linalg.inv(cam_H_m2c_ref))

        print('-----------------------------')
        print(f"Cam: {cam_H_c2w}")
        print('-----------------------------')

        # transform from OpenCV to blender coords
        cam_H_c2w = change_source_coordinate_frame_of_transformation_matrix(cam_H_c2w, source_frame)

        return cam_H_c2w

    @staticmethod
    def set_object_pose(cur_obj: bpy.types.Object, inst: dict, scale: float):
        """ Set object pose for current obj

        :param cur_obj: Current object.
        :param inst: instance from BOP scene_gt file.
        :param scale: factor to transform set pose in mm or meters.
        """

        cam_H_m2c = np.eye(4)
        cam_H_m2c[:3, :3] = np.array(inst['cam_R_m2c']).reshape(3, 3)
        cam_H_m2c[:3, 3] = np.array(inst['cam_t_m2c']).reshape(3) * scale

        # world = camera @ i=0
        cam_H_m2w = cam_H_m2c

        print('-----------------------------')
        print(f"Cam: {cam_H_m2w}")
        print('-----------------------------')

        cur_obj.set_local2world_mat(Matrix(cam_H_m2w))
        cur_obj.set_scale(Vector((scale, scale, scale)))

    @staticmethod
    def insert_key_frames(obj: bpy.types.Object, frame_id: int):
        """ Insert key frames for given object pose.

        :param obj: Loaded object.
        :param frame_id: The frame number where key frames should be inserted.
        """

        obj.set_location(obj.get_location(), frame_id)
        obj.set_rotation_euler(obj.get_rotation_euler(), frame_id)

    @staticmethod
    def get_ref_cam_extrinsics_intrinsics(sc_camera: dict, cam_id: int, insts: dict,
                                          scale: float) -> Tuple[np.ndarray, np.ndarray]:
        """ Get camK and transformation from object instance 0 to camera cam_id as reference.

        :param sc_camera: BOP scene_camera file.
        :param cam_id: BOP camera id.
        :param insts: Instance from BOP scene_gt file.
        :param scale: Factor to transform get pose in mm or meters.
        :return (camK, cam_H_m2c_ref): loaded camera matrix. Loaded object to camera transformation.
        """

        cam_K = np.array(sc_camera[str(cam_id)]['cam_K']).reshape(3, 3)
        cam_H_m2c_ref = np.eye(4)
        cam_H_m2c_ref[:3, :3] = np.array(insts[0]['cam_R_m2c']).reshape(3, 3)
        cam_H_m2c_ref[:3, 3] = np.array(insts[0]['cam_t_m2c']).reshape(3) * scale

        return cam_K, cam_H_m2c_ref

    @staticmethod
    def get_loaded_obj(model_path: str) -> Optional[bpy.types.Object]:
        """ Returns the object if it has already been loaded.

        :param model_path: Model path of the new object.
        :return: Object if found, else return None.
        """
        for loaded_obj in bpy.context.scene.objects:
            if 'model_path' in loaded_obj and loaded_obj['model_path'] == model_path:
                return loaded_obj
        return None

    @staticmethod
    def load_mesh(obj_id: int, model_p: dict, bop_dataset_name: str, scale: float = 1) -> MeshObject:
        """ Loads BOP mesh and sets category_id.

        :param obj_id: The obj_id of the BOP Object.
        :param model_p: model parameters defined in dataset_params.py in bop_toolkit.
        :param bop_dataset_name: The name of the used bop dataset.
        :param scale: factor to transform set pose in mm or meters.
        :return: Loaded mesh object.
        """

        model_path = model_p["model_tpath"].format(**{"obj_id": obj_id})

        # if the object was not previously loaded - load it, if duplication is allowed - duplicate it
        duplicated = model_path in _BopLoader.CACHED_OBJECTS
        objs = load_obj(model_path, cached_objects=_BopLoader.CACHED_OBJECTS)
        assert (
            len(objs) == 1
        ), f"Loading object from '{model_path}' returned more than one mesh"
        cur_obj = objs[0]

        if duplicated:
            # See issue https://github.com/DLR-RM/BlenderProc/issues/590
            for i, material in enumerate(cur_obj.get_materials()):
                material_dup = material.duplicate()
                cur_obj.set_material(i, material_dup)

        # Change Material name to be backward compatible
        cur_obj.get_materials()[-1].set_name("bop_" + bop_dataset_name + "_vertex_col_material")
        cur_obj.set_scale(Vector((scale, scale, scale)))
        cur_obj.set_cp("category_id", obj_id)
        cur_obj.set_cp("model_path", model_path)
        cur_obj.set_cp("is_bop_object", True)
        cur_obj.set_cp("bop_dataset_name", bop_dataset_name)

        return cur_obj
