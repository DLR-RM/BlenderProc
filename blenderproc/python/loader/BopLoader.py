import os
import sys
from random import choice
from typing import List, Union

import bpy
import numpy as np
from mathutils import Matrix, Vector

from blenderproc.python.utility.SetupUtility import SetupUtility
import blenderproc.python.camera.CameraUtility as CameraUtility
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.utility.Utility import Utility
from blenderproc.python.utility.MathUtility import change_source_coordinate_frame_of_transformation_matrix
from blenderproc.python.types.MaterialUtility import Material


def load_bop_objs(bop_dataset_path: str, model_type: str = "", obj_ids: list = [], sample_objects: bool = False, num_of_objs_to_sample: int = None, 
                  obj_instances_limit: int = -1, mm2m: bool = False, move_origin_to_x_y_plane: bool = False, temp_dir: str = None, ) -> List[MeshObject]:
    """ Loads all or a subset of 3D models of any BOP dataset

    :param bop_dataset_path: Full path to a specific bop dataset e.g. /home/user/bop/tless.
    :param model_type: Optionally, specify type of BOP model. Available: [reconst, cad or eval].
    :param obj_ids: List of object ids to load. Default: [] (load all objects from the given BOP dataset)
    :param sample_objects: Toggles object sampling from the specified dataset.
    :param num_of_objs_to_sample: Amount of objects to sample from the specified dataset. If this amount is bigger than the dataset
                                  actually contains, then all objects will be loaded.
    :param obj_instances_limit: Limits the amount of object copies when sampling. Default: -1 (no limit).
    :param mm2m: Specify whether to convert poses and models to meters.
    :param move_origin_to_x_y_plane: Move center of the object to the lower side of the object, this will not work when used in combination with
                                     pose estimation tasks! This is designed for the use-case where BOP objects are used as filler objects in
                                     the background.
    :param temp_dir: A temp directory which is used for writing the temporary .ply file.
    :return: The list of loaded mesh objects.
    """

    bop_path, bop_dataset_name = BopLoader._setup_bop_toolkit(bop_dataset_path)
    
    from bop_toolkit_lib import dataset_params
    model_p = dataset_params.get_model_params(bop_path, bop_dataset_name, model_type=model_type if model_type else None)
    
    # temp_dir, scale, bop_dataset_name, has_external_texture, model_p = setup_bop(bop_dataset_path, temp_dir, model_type, mm2m)
    if temp_dir is None:
        temp_dir = Utility.get_temporary_directory()
        
    scale = 0.001 if mm2m else 1
    has_external_texture = bop_dataset_name in ["ycbv", "ruapc"]
    allow_duplication = obj_ids or sample_objects
    
    obj_ids = obj_ids if obj_ids else model_p['obj_ids']
    
    loaded_objects = []
    # if sampling is enabled
    if sample_objects:
        loaded_ids = {}
        loaded_amount = 0
        if obj_instances_limit != -1 and len(obj_ids) * obj_instances_limit < num_of_objs_to_sample:
            raise RuntimeError("{}'s {} split contains {} objects, {} object where requested to sample with "
                               "an instances limit of {}. Raise the limit amount or decrease the requested "
                               "amount of objects.".format(bop_dataset_path, split, len(obj_ids),
                                                           num_of_objs_to_sample,
                                                           obj_instances_limit))
        while loaded_amount != num_of_objs_to_sample:
            random_id = choice(obj_ids)
            if random_id not in loaded_ids.keys():
                loaded_ids.update({random_id: 0})
            # if there is no limit or if there is one, but it is not reached for this particular object
            if obj_instances_limit == -1 or loaded_ids[random_id] < obj_instances_limit:
                cur_obj = BopLoader._load_mesh(random_id, model_p, bop_dataset_name, has_external_texture, temp_dir, allow_duplication, scale)
                loaded_ids[random_id] += 1
                loaded_amount += 1
                loaded_objects.append(cur_obj)
            else:
                print("ID {} was loaded {} times with limit of {}. Total loaded amount {} while {} are "
                      "being requested".format(random_id, loaded_ids[random_id], obj_instances_limit,
                                               loaded_amount, num_of_objs_to_sample))
    else:
        for obj_id in obj_ids:
            cur_obj = BopLoader._load_mesh(obj_id, model_p, bop_dataset_name, has_external_texture, temp_dir, allow_duplication, scale)
            loaded_objects.append(cur_obj)
    # move the origin of the object to the world origin and on top of the X-Y plane
    # makes it easier to place them later on, this does not change the `.location`
    # This is only useful if the BOP objects are not used in a pose estimation scenario.
    if move_origin_to_x_y_plane:
        for obj in loaded_objects:
            obj.move_origin_to_bottom_mean_point()
            
    return loaded_objects
    
def load_bop_scene(bop_dataset_path: str, scene_id: int, model_type: str = "", cam_type: str = "", split: str = "test", source_frame: list = ["X", "-Y", "-Z"], mm2m: bool = False, temp_dir: str = None) -> List[MeshObject]:
    """ Replicate a BOP scene from the given dataset: load scene objects, object poses, camera intrinsics and extrinsics

    - Interfaces with the bob_toolkit, allows loading of train, val and test splits
    - Relative camera poses are loaded/computed with respect to a reference model
    - Sets real camera intrinsics

    :param bop_dataset_path: Full path to a specific bop dataset e.g. /home/user/bop/tless.
    :param scene_id: Specify BOP dataset scene to synthetically replicate. Default: -1 (no scene is replicated,
                     only BOP Objects are loaded).
    :param model_type: Optionally, specify type of BOP model.  Available: [reconst, cad or eval].
    :param cam_type: Camera type. If not defined, dataset-specific default camera type is used.
    :param split: Optionally, test or val split depending on BOP dataset.
    :param source_frame: Can be used if the given positions and rotations are specified in frames different from the blender
                        frame. Has to be a list of three strings. Example: ['X', '-Z', 'Y']: Point (1,2,3) will be transformed
                        to (1, -3, 2). Available: ['X', 'Y', 'Z', '-X', '-Y', '-Z'].
    :param mm2m: Specify whether to convert poses and models to meters.
    :param temp_dir: A temp directory which is used for writing the temporary .ply file.
    :return: The list of loaded mesh objects.
    """

    bop_path, bop_dataset_name = BopLoader._setup_bop_toolkit(bop_dataset_path)
    
    from bop_toolkit_lib import dataset_params, inout
    model_p = dataset_params.get_model_params(bop_path, bop_dataset_name, model_type=model_type if model_type else None)
    try:
        split_p = dataset_params.get_split_params(bop_path, bop_dataset_name, split=split, split_type=cam_type if cam_type else None)
    except ValueError:
        raise Exception("Wrong path or {} split does not exist in {}.".format(split, bop_dataset_name))
    sc_gt = inout.load_scene_gt(split_p['scene_gt_tpath'].format(**{'scene_id': scene_id}))
    sc_camera = inout.load_json(split_p['scene_camera_tpath'].format(**{'scene_id': scene_id}))
    
    if temp_dir is None:
        temp_dir = Utility.get_temporary_directory()
        
    scale = 0.001 if mm2m else 1
    has_external_texture = bop_dataset_name in ["ycbv", "ruapc"]
    
    for i, (cam_id, insts) in enumerate(sc_gt.items()):
        cam_K, cam_H_m2c_ref = BopLoader._get_ref_cam_extrinsics_intrinsics(sc_camera, cam_id, insts, scale)

        if i == 0:
            # define world = first camera
            cam_H_m2w_ref = cam_H_m2c_ref.copy()

            cur_objs = []
            # load scene objects and set their poses
            for inst in insts:
                cur_objs.append(BopLoader._load_mesh(inst['obj_id'], model_p, bop_dataset_name, has_external_texture, temp_dir, False, scale))
                BopLoader.set_object_pose(cur_objs[-1], inst, scale)

        cam_H_c2w = BopLoader._compute_camera_to_world_trafo(cam_H_m2w_ref, cam_H_m2c_ref, source_frame)
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
            BopLoader._insert_key_frames(cur_obj, frame_id)

    return cur_objs

def load_bop_intrinsics(bop_dataset_path: str, split: str = "test", cam_type: str = "") -> tuple[np.ndarray, int, int]:
    """
    Load and set the camera matrix and image resolution of a specified BOP dataset

    :param bop_dataset_path: Full path to a specific bop dataset e.g. /home/user/bop/tless.
    :param split: Optionally, train, test or val split depending on BOP dataset, defaults to "test"
    :param cam_type: Camera type. If not defined, dataset-specific default camera type is used.
    :returns: camera matrix K, W, H
    """
    
    bop_path, bop_dataset_name = BopLoader._setup_bop_toolkit(bop_dataset_path)   
    
    from bop_toolkit_lib import dataset_params
    cam_p = dataset_params.get_camera_params(bop_path, bop_dataset_name, cam_type=cam_type if cam_type else None)
        
    try:
        split_p = dataset_params.get_split_params(bop_path, bop_dataset_name, split=split, split_type=cam_type if cam_type else None)
    except ValueError:
        raise Exception("Wrong path or {} split does not exist in {}.".format(split, bop_dataset_name))
    
    # TLESS exception because images are cropped
    if bop_dataset_name in ['tless']:
        cam_p['K'][0, 2] = split_p['im_size'][0] / 2
        cam_p['K'][1, 2] = split_p['im_size'][1] / 2

    # set camera intrinsics
    CameraUtility.set_intrinsics_from_K_matrix(cam_p['K'], split_p['im_size'][0], split_p['im_size'][1])
    
    return cam_p['K'], split_p['im_size'][0], split_p['im_size'][1]

class BopLoader:

    @staticmethod
    def _setup_bop_toolkit(bop_dataset_path: str) -> tuple[str, str]:
        """
        Install the bop_toolkit from Github and set an environment variable pointing to the BOP datasets 

        :param cam_H_m2c_ref: (4x4) Homog trafo from object to camera coords.
        :return (bop_path, bop_dataset_name): Path to BOP datasets and BOP dataset name
        """

        bop_dataset_name = os.path.basename(bop_dataset_path)
        bop_path = os.path.dirname(bop_dataset_path)

        print("bob: {}, dataset_path: {}".format(bop_dataset_path, bop_path))
        print("dataset: {}".format(bop_dataset_name))

        if not os.path.exists(bop_path):
            raise ValueError("It seems the BOP dataset does not exist under the given path {}".format(bop_dataset_path))

        # Install bop_toolkit_lib
        SetupUtility.setup_pip(["git+https://github.com/thodan/bop_toolkit"])
        os.environ["BOP_PATH"] = bop_path

        return bop_path, bop_dataset_name 

    @staticmethod
    def _compute_camera_to_world_trafo(cam_H_m2w_ref: np.array, cam_H_m2c_ref: np.array, source_frame: list) -> np.ndarray:
        """ Returns camera to world transformation in blender coords.

        :param cam_H_m2c_ref: (4x4) Homog trafo from object to camera coords.
        :param cam_H_m2w_ref: (4x4) Homog trafo from object to world coords.
        :param source_frame: Can be used if the given positions and rotations are specified in frames different from the blender frame.
        :return: cam_H_c2w: (4x4) Homog trafo from camera to world coords.
        """

        cam_H_c2w = np.dot(cam_H_m2w_ref, np.linalg.inv(cam_H_m2c_ref))

        print('-----------------------------')
        print("Cam: {}".format(cam_H_c2w))
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
        print("Model: {}".format(cam_H_m2w))
        print('-----------------------------')

        cur_obj.set_local2world_mat(Matrix(cam_H_m2w))
        cur_obj.set_scale(Vector((scale, scale, scale)))

    @staticmethod
    def _insert_key_frames(obj: bpy.types.Object, frame_id: int):
        """ Insert key frames for given object pose.

        :param obj: Loaded object.
        :param frame_id: The frame number where key frames should be inserted.
        """

        obj.set_location(obj.get_location(), frame_id)
        obj.set_rotation_euler(obj.get_rotation(), frame_id)

    @staticmethod
    def _get_ref_cam_extrinsics_intrinsics(sc_camera: dict, cam_id: int, insts: dict, scale: float) -> np.ndarray:
        """ Get camK and transformation from object instance 0 to camera cam_id as reference.

        :param sc_camera: BOP scene_camera file.
        :param cam_id: BOP camera id.
        :param insts: Instance from BOP scene_gt file.
        :param scale: Factor to transform get pose in mm or meters.
        :return (camK, cam_H_m2c_ref): loaded camera matrix. Loaded object to camera transformation.
        """

        cam_K = np.array(sc_camera[str(cam_id)]['cam_K']).reshape(3,3)
        cam_H_m2c_ref = np.eye(4)
        cam_H_m2c_ref[:3,:3] = np.array(insts[0]['cam_R_m2c']).reshape(3,3) 
        cam_H_m2c_ref[:3, 3] = np.array(insts[0]['cam_t_m2c']).reshape(3) * scale

        return (cam_K, cam_H_m2c_ref)

    @staticmethod
    def _get_loaded_obj(model_path: str) -> bpy.types.Object:
        """ Returns the object if it has already been loaded.
 
        :param model_path: Model path of the new object.
        :return: Object if found, else return None.
        """
        for loaded_obj in bpy.context.scene.objects:
            if 'model_path' in loaded_obj and loaded_obj['model_path'] == model_path:
                return loaded_obj
        return


    @staticmethod
    def _load_mesh(obj_id: int, model_p: dict, bop_dataset_name: str, has_external_texture: bool, temp_dir: str, allow_duplication: bool, scale: float = 1) -> MeshObject:
        """ Loads BOP mesh and sets category_id.

        :param obj_id: The obj_id of the BOP Object.
        :param model_p: model parameters defined in dataset_params.py in bop_toolkit.
        :param bop_dataset_name: The name of the used bop dataset.
        :param has_external_texture: Set to True, if the object has an external texture.
        :param temp_dir: A temp directory which is used for writing the temporary .ply file.
        :param allow_duplication: If True, the object is duplicated if it already exists.
        :param scale: factor to transform set pose in mm or meters.
        :return: Loaded mesh object.
        """

        model_path = model_p['model_tpath'].format(**{'obj_id': obj_id})

        texture_file_path = ""  # only needed for ycbv objects

        # Gets the objects if it is already loaded         
        cur_obj = BopLoader._get_loaded_obj(model_path)
        # if the object was not previously loaded - load it, if duplication is allowed - duplicate it
        if cur_obj is None:
            if has_external_texture:
                if os.path.exists(model_path):
                    new_file_ply_content = ""
                    with open(model_path, "r") as file:
                        new_file_ply_content = file.read()
                        texture_pos = new_file_ply_content.find("comment TextureFile ") + len("comment TextureFile ")
                        texture_file_name = new_file_ply_content[texture_pos:
                                                                 new_file_ply_content.find("\n", texture_pos)]
                        texture_file_path = os.path.join(os.path.dirname(model_path), texture_file_name)
                        new_file_ply_content = new_file_ply_content.replace("property float texture_u",
                                                                            "property float s")
                        new_file_ply_content = new_file_ply_content.replace("property float texture_v",
                                                                            "property float t")
                    model_name = os.path.basename(model_path)
                    tmp_ply_file = os.path.join(temp_dir, model_name)
                    with open(tmp_ply_file, "w") as file:
                        file.write(new_file_ply_content)
                    bpy.ops.import_mesh.ply(filepath=tmp_ply_file)
                    cur_obj = bpy.context.selected_objects[-1]
            else:
                bpy.ops.import_mesh.ply(filepath=model_path)
                cur_obj = bpy.context.selected_objects[-1]
        elif allow_duplication:
            bpy.ops.object.duplicate({"object": cur_obj, "selected_objects": [cur_obj]})
            cur_obj = bpy.context.selected_objects[-1]

        cur_obj.scale = Vector((scale, scale, scale))
        cur_obj['category_id'] = obj_id
        cur_obj['model_path'] = model_path
        cur_obj["is_bop_object"] = True
        cur_obj["bop_dataset_name"] = bop_dataset_name
        
        if not has_external_texture:
            mat = BopLoader._load_materials(cur_obj, bop_dataset_name)
            mat.map_vertex_color()
        elif texture_file_path != "":
            # ycbv objects contain normal image textures, which should be used instead of the vertex colors
            BopLoader._load_texture(cur_obj, texture_file_path, bop_dataset_name)
        return MeshObject(cur_obj)

    @staticmethod
    def _load_materials(cur_obj: bpy.types.Object, bop_dataset_name: str) -> Material:
        """ Loads / defines materials, e.g. vertex colors.
        
        :param cur_obj: The object to use.
        :param bop_dataset_name: The name of the used bop dataset.
        :return: Material with vertex color.
        """

        mat = cur_obj.data.materials.get("Material")
        
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name="bop_" + bop_dataset_name + "_vertex_col_material")

        mat.use_nodes = True

        if cur_obj.data.materials:
            # assign to 1st material slot
            cur_obj.data.materials[0] = mat
        else:
            # no slots
            cur_obj.data.materials.append(mat)

        return Material(mat)

    @staticmethod
    def _load_texture(cur_obj: bpy.types.Object, texture_file_path: str, bop_dataset_name: str):
        """
        Load the textures for the ycbv objects, only those contain texture information

        :param cur_obj: The object to use.
        :param texture_file_path: path to the texture file (most likely ".png")
        :param bop_dataset_name: The name of the used bop dataset.
        """
        mat = bpy.data.materials.new(name="bop_" + bop_dataset_name + "_texture_material")

        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        color_image = nodes.new('ShaderNodeTexImage')
        if not os.path.exists(texture_file_path):
            raise Exception("The texture path for the ycbv object could not be loaded from the "
                            "file: {}".format(texture_file_path))
        color_image.image = bpy.data.images.load(texture_file_path, check_existing=True)

        principled = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
        links.new(color_image.outputs["Color"], principled.inputs["Base Color"])

        if cur_obj.data.materials:
            # assign to 1st material slot
            cur_obj.data.materials[0] = mat
        else:
            # no slots
            cur_obj.data.materials.append(mat)
