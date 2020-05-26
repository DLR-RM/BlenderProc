import math
import os
import sys
from random import choice

import bpy
import numpy as np
from mathutils import Matrix, Vector

from src.camera.CameraModule import CameraModule
from src.loader.Loader import Loader
from src.utility.Utility import Utility
from src.utility.Config import Config


class BopLoader(Loader):
    """ Loads the 3D models of any BOP dataset and allows replicating BOP scenes
    
    - Interfaces with the bob_toolkit, allows loading of train, val and test splits
    - Relative camera poses are loaded/computed with respect to a reference model
    - Sets real camera intrinsics

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "cam_type", "Camera type. Type: string. Optional. Default value: ''."
       "sys_paths", "System paths to append. Type: list."
       "num_of_objs_to_sample", "Number of the objects to sample. Type: int."
       "bop_dataset_path", "Full path to a specific bop dataset e.g. /home/user/bop/tless. Type: string."
       "mm2m", "Specify whether to convert poses and models to meters. Type: bool. Optional. Default: False."
       "split", "Optionally, test or val split depending on BOP dataset. Type: string. Optional. Default: test."
       "scene_id", "Optionally, specify BOP dataset scene to synthetically replicate. Type: int. Default: -1 (no scene "
                   "is replicated, only BOP Objects are loaded)."
       "sample_objects", "Toggles object sampling from the specified dataset. Type: boolean. Default: False."
       "num_of_objs_to_sample", "Amount of objects to sample from the specified dataset. Type: int. If this amount is "
                                "bigger than the dataset actually contains, then all objects will be loaded. Type: int."
       "obj_instances_limit", "Limits the amount of object copies when sampling. Type: int. Default: -1 (no limit)."
       "obj_ids", "List of object ids to load. Type: list. Default: [] (all objects from the given BOP dataset if "
                  "scene_id is not specified)."
       "model_type", "Optionally, specify type of BOP model. Type: string. Default: "". Available: [reconst, cad or eval]."
    """

    def __init__(self, config):
        Loader.__init__(self, config)
        sys_paths = self.config.get_list("sys_paths")
        for sys_path in sys_paths:
            if 'bop_toolkit' in sys_path:
                sys.path.append(sys_path)

        self.sample_objects = self.config.get_bool("sample_objects", False)
        if self.sample_objects:
            self.num_of_objs_to_sample = self.config.get_int("num_of_objs_to_sample")
            self.obj_instances_limit = self.config.get_int("obj_instances_limit", -1)

        self.cam_type = self.config.get_string("cam_type", "")
        self.bop_dataset_path = self.config.get_string("bop_dataset_path")
        self.scene_id = self.config.get_int("scene_id", -1)
        self.obj_ids = self.config.get_list("obj_ids", [])
        if self.obj_ids or self.sample_objects:
            self.allow_duplication = True
        else:
            self.allow_duplication = False
        self.split = self.config.get_string("split", "test")
        self.model_type = self.config.get_string("model_type", "")
        self.scale = 0.001 if self.config.get_bool("mm2m", False) else 1
        self.bop_dataset_name = os.path.basename(self.bop_dataset_path)
        self._has_external_texture = self.bop_dataset_name in ["ycbv", "ruapc"]

    def run(self):
        """ Load BOP data """

        datasets_path = os.path.dirname(self.bop_dataset_path)
        dataset = os.path.basename(self.bop_dataset_path)
        
        print("bob: {}, dataset_path: {}".format(self.bop_dataset_path, datasets_path))
        print("dataset: {}".format(dataset))

        try:
            from bop_toolkit_lib import dataset_params, inout
        except ImportError as error:
            print('ERROR: Please download the bop_toolkit package and add it to sys_paths in config!')
            print('https://github.com/thodan/bop_toolkit')
            raise error

        model_p = dataset_params.get_model_params(datasets_path, dataset, model_type=self.model_type if self.model_type else None)
        cam_p = dataset_params.get_camera_params(datasets_path, dataset, cam_type=self.cam_type if self.cam_type else None)
        bpy.data.scenes["Scene"]["num_labels"] = len(model_p['obj_ids'])
        
        try:
            split_p = dataset_params.get_split_params(datasets_path, dataset, split=self.split)
        except ValueError:
            raise Exception("Wrong path or {} split does not exist in {}.".format(self.split, dataset))
        
        bpy.context.scene.world["category_id"] = 0
        bpy.context.scene.render.resolution_x = cam_p['im_size'][0]
        bpy.context.scene.render.resolution_y = cam_p['im_size'][1]

        # Collect camera and camera object
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data
        cam['loaded_resolution'] = cam_p['im_size'][0], cam_p['im_size'][1]
        # load default intrinsics from camera.json
        cam['loaded_intrinsics'] = cam_p['K']
        
        config = Config({})
        camera_module = CameraModule(config)
        camera_module._set_cam_intrinsics(cam, config)

        loaded_objects = []

        # only load all/selected objects here, use other modules for setting poses
        # e.g. camera.CameraSampler / object.ObjectPoseSampler
        if self.scene_id == -1:
            obj_ids = self.obj_ids if self.obj_ids else model_p['obj_ids']
            # if sampling is enabled
            if self.sample_objects:
                loaded_ids = {}
                loaded_amount = 0
                if self.obj_instances_limit != -1 and len(obj_ids) * self.obj_instances_limit < self.num_of_objs_to_sample:
                    raise RuntimeError("{}'s {} split contains {} objects, {} object where requested to sample with "
                                       "an instances limit of {}. Raise the limit amount or decrease the requested "
                                       "amount of objects.".format(self.bop_dataset_path, self.split, len(obj_ids),
                                                                   self.num_of_objs_to_sample,
                                                                   self.obj_instances_limit))
                while loaded_amount != self.num_of_objs_to_sample:
                    random_id = choice(obj_ids)
                    if random_id not in loaded_ids.keys():
                        loaded_ids.update({random_id: 0})
                    # if there is no limit or if there is one, but it is not reached for this particular object
                    if self.obj_instances_limit == -1 or loaded_ids[random_id] < self.obj_instances_limit:
                        cur_obj = self._load_mesh(random_id, model_p, scale=self.scale)
                        loaded_ids[random_id] += 1
                        loaded_amount += 1
                        loaded_objects.append(cur_obj)
                    else:
                        print("ID {} was loaded {} times with limit of {}. Total loaded amount {} while {} are "
                              "being requested".format(random_id, loaded_ids[random_id], self.obj_instances_limit,
                                                       loaded_amount, self.num_of_objs_to_sample))
            else:
                for obj_id in obj_ids:
                    cur_obj = self._load_mesh(obj_id, model_p, scale=self.scale)
                    loaded_objects.append(cur_obj)
            self._set_properties(loaded_objects)

        # replicate scene: load scene objects, object poses, camera intrinsics and camera poses
        else:
            sc_gt = inout.load_scene_gt(split_p['scene_gt_tpath'].format(**{'scene_id': self.scene_id}))
            sc_camera = inout.load_json(split_p['scene_camera_tpath'].format(**{'scene_id': self.scene_id}))
            for i, (cam_id, insts) in enumerate(sc_gt.items()):
                cam_K, cam_H_m2c_ref = self._get_ref_cam_extrinsics_intrinsics(sc_camera, cam_id, insts, self.scale)

                if i == 0:
                    # define world = first camera
                    cam_H_m2w_ref = cam_H_m2c_ref.copy()

                    cur_objs = []
                    # load scene objects and set their poses
                    for inst in insts:                           
                        cur_objs.append(self._load_mesh(inst['obj_id'], model_p, scale=self.scale))
                        self.set_object_pose(cur_objs[-1], inst, self.scale)
                        

                cam_H_c2w = self._compute_camera_to_world_trafo(cam_H_m2w_ref, cam_H_m2c_ref)
                #set camera intrinsics and extrinsics 
                config = Config({"cam2world_matrix": list(cam_H_c2w.flatten()), "cam_K": list(cam_K.flatten())})
                camera_module._set_cam_intrinsics(cam, config)
                camera_module._set_cam_extrinsics(cam_ob, config)

                # Store new cam pose as next frame
                frame_id = bpy.context.scene.frame_end
                # Copy object poses to next key frame (to be sure)
                for cur_obj in cur_objs:                           
                    self._insert_key_frames(cur_obj, frame_id)
                camera_module._insert_key_frames(cam, cam_ob, frame_id)
                bpy.context.scene.frame_end = frame_id + 1

    def _compute_camera_to_world_trafo(self, cam_H_m2w_ref, cam_H_m2c_ref):
        """ Returns camera to world transformation in blender coords.

        :param cam_H_m2c_ref: (4x4) Homog trafo from object to camera coords. Type: ndarray.
        :param cam_H_m2w_ref: (4x4) Homog trafo from object to world coords. Type: ndarray.
        :return: cam_H_c2w: (4x4) Homog trafo from camera to world coords. Type: mathutils.Matrix.
        """

        cam_H_c2w = np.dot(cam_H_m2w_ref, np.linalg.inv(cam_H_m2c_ref))

        print('-----------------------------')
        print("Cam: {}".format(cam_H_c2w))
        print('-----------------------------')

        # transform from OpenCV to blender coords
        cam_H_c2w = cam_H_c2w @ Matrix.Rotation(math.radians(180), 4, "X")

        return cam_H_c2w

    def set_object_pose(self, cur_obj, inst, scale):
        """ Set object pose for current obj

        :param cur_obj: Current object. Type: bpy.types.Object.
        :param inst: instance from BOP scene_gt file. Type: dict.
        :param scale : factor to transform set pose in mm or meters. Type: dict.
        """

        cam_H_m2c = np.eye(4)
        cam_H_m2c[:3, :3] = np.array(inst['cam_R_m2c']).reshape(3, 3)
        cam_H_m2c[:3, 3] = np.array(inst['cam_t_m2c']).reshape(3) * scale

        # world = camera @ i=0
        cam_H_m2w = cam_H_m2c

        print('-----------------------------')
        print("Model: {}".format(cam_H_m2w))
        print('-----------------------------')

        cur_obj.matrix_world = Matrix(cam_H_m2w)
        cur_obj.scale = Vector((scale, scale, scale))

    def _insert_key_frames(self, obj, frame_id):
        """ Insert key frames for given object pose.

        :param obj: Loaded object. Type: bpy.types.Object.
        :param frame_id: The frame number where key frames should be inserted. Type: int.
        """

        obj.keyframe_insert(data_path='location', frame=frame_id)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame_id)

    def _get_ref_cam_extrinsics_intrinsics(self, sc_camera, cam_id, insts, scale):
        """ Get camK and transformation from object instance 0 to camera cam_id as reference.

        :param sc_camera: BOP scene_camera file. Type: dict.
        :param cam_id: BOP camera id. Type: int.
        :param insts: Instance from BOP scene_gt file. Type: dict.
        :param scale: Factor to transform get pose in mm or meters. Type: int.
        :return camK : loaded camera matrix. Type: ndarray.
        :return cam_H_m2c_ref: loaded object to camera transformation. Type: ndarray.
        """

        cam_K = np.array(sc_camera[str(cam_id)]['cam_K']).reshape(3,3)
        cam_H_m2c_ref = np.eye(4)
        cam_H_m2c_ref[:3,:3] = np.array(insts[0]['cam_R_m2c']).reshape(3,3) 
        cam_H_m2c_ref[:3, 3] = np.array(insts[0]['cam_t_m2c']).reshape(3) * scale

        return (cam_K, cam_H_m2c_ref)

    def _get_loaded_obj(self, model_path):
        """ Returns the object if it has already been loaded.
 
        :param model_path: Model path of the new object. Type: string.
        :return: Object if found, else return None. Type: bpy.types.Object/None.
        """
        for loaded_obj in bpy.context.scene.objects:
            if 'model_path' in loaded_obj and loaded_obj['model_path'] == model_path:
                return loaded_obj
        return


    def _load_mesh(self, obj_id, model_p, scale=1):
        """ Loads BOP mesh and sets category_id.

        :param obj_id: The obj_id of the BOP Object. Type: int.
        :param model_p: model parameters defined in dataset_params.py in bop_toolkit. Type: dict.
        :return: Current object. Type: bpy.types.Object.
        """

        model_path = model_p['model_tpath'].format(**{'obj_id': obj_id})

        texture_file_path = ""  # only needed for ycbv objects

        # Gets the objects if it is already loaded         
        cur_obj = self._get_loaded_obj(model_path)
        # if the object was not previously loaded - load it, if duplication is allowed - duplicate it
        if cur_obj is None:
            if self._has_external_texture:
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
                    tmp_ply_file = os.path.join(Utility.get_temporary_directory(self.config), model_name)
                    with open(tmp_ply_file, "w") as file:
                        file.write(new_file_ply_content)
                    bpy.ops.import_mesh.ply(filepath=tmp_ply_file)
                    cur_obj = bpy.context.selected_objects[-1]
            else:
                bpy.ops.import_mesh.ply(filepath=model_path)
                cur_obj = bpy.context.selected_objects[-1]
        elif self.allow_duplication:
            bpy.ops.object.duplicate({"object": cur_obj, "selected_objects": [cur_obj]})
            cur_obj = bpy.context.selected_objects[-1]

        cur_obj.scale = Vector((scale, scale, scale))
        cur_obj['category_id'] = obj_id
        cur_obj['model_path'] = model_path
        if not self._has_external_texture:
            mat = self._load_materials(cur_obj)
            self._link_col_node(mat)
        elif texture_file_path != "":
            # ycbv objects contain normal image textures, which should be used instead of the vertex colors
            self._load_texture(cur_obj, texture_file_path)
        cur_obj["is_bop_object"] = True
        cur_obj["bop_dataset_name"] = self.bop_dataset_name
        return cur_obj

    def _load_materials(self, cur_obj):
        """ Loads / defines materials, e.g. vertex colors.
        
        :param cur_obj: The object to use. Type: bpy.types.Object.
        :return: Material with vertex color. Type: bpy.types.Material.
        """

        mat = cur_obj.data.materials.get("Material")
        
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name="bop_" + self.bop_dataset_name + "_vertex_col_material")

        mat.use_nodes = True

        if cur_obj.data.materials:
            # assign to 1st material slot
            cur_obj.data.materials[0] = mat
        else:
            # no slots
            cur_obj.data.materials.append(mat)

        return mat

    def _load_texture(self, cur_obj, texture_file_path):
        """
        Load the textures for the ycbv objects, only those contain texture information

        :param cur_obj: The object to use. Type: bpy.types.Object.
        :param texture_file_path: path to the texture file (most likely ".png")
        """
        mat = bpy.data.materials.new(name="bop_" + self.bop_dataset_name + "_texture_material")

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


    def _link_col_node(self, mat):
        """ Links a color attribute node to a Principled BSDF node.

        :param mat: The material to use. Type: bpy.types.Material.
        """
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        attr_node = nodes.new(type='ShaderNodeAttribute')
        attr_node.attribute_name = 'Col'

        principled_node = nodes.get("Principled BSDF")

        links.new(attr_node.outputs['Color'], principled_node.inputs['Base Color'])
