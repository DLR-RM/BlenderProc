import json
import os
from mathutils import Matrix, Vector, Euler
import math
import csv
import bpy
import numpy as np
import sys
from copy import deepcopy

from src.main.Module import Module
from src.utility.Utility import Utility
from src.utility.Config import Config
from src.camera.CameraModule import CameraModule

class BopLoader(Module):
    """ Loads the 3D models of any BOP dataset and allows replicating BOP scenes
    
    - Interfaces with the bob_toolkit, allows loading of train, val and test splits
    - Relative camera poses are loaded/computed with respect to a reference model
    - Sets real camera intrinsics

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "bop_dataset_path", "Full path to a specific bop dataset e.g. /home/user/bop/tless"
       "mm2m", "Specify whether to convert poses to meters"
       "split", "Optionally, test or val split depending on BOP dataset"
       "scene_id", "Optionally, specify BOP dataset scene to synthetically replicate. (default = -1 means no scene is replicated, only BOP Objects are loaded)"
       "obj_ids", "If scene_id is not specified (scene_id: -1): List of object ids to load (default: All objects from the BOP dataset)"
       "model_type", "Type of BOP model, e.g. reconstruction or CAD"
    """

    def __init__(self, config):
        Module.__init__(self, config)

        for sys_path in self.config.get_list("sys_paths"):
            if 'bop_toolkit' in sys_path:
                sys.path.append(sys_path)
        
    def run(self):
        
        bop_dataset_path = self.config.get_string("bop_dataset_path")
        scene_id = self.config.get_int("scene_id", -1)
        obj_ids = self.config.get_list("obj_ids", [])
        split = self.config.get_string("split", "test")
        model_type = self.config.get_string("model_type", "")
        cam_type = self.config.get_string("cam_type", "")
        mm2m = 0.001 if self.config.get_bool("mm2m", False) else 1
        datasets_path = os.path.dirname(bop_dataset_path)
        dataset = os.path.basename(bop_dataset_path)
        
        print("bob: {}, dataset_path: {}".format(bop_dataset_path, datasets_path))
        print("dataset: {}".format(dataset))

        try:
            from bop_toolkit_lib import dataset_params, inout
        except ImportError as error:
            print('ERROR: Please download the bop_toolkit package and add it to sys_paths in config!')
            print('https://github.com/thodan/bop_toolkit')
            raise error

        model_p = dataset_params.get_model_params(datasets_path, dataset, model_type=model_type if model_type else None)
        cam_p = dataset_params.get_camera_params(datasets_path, dataset, cam_type=cam_type if cam_type else None)
        bpy.data.scenes["Scene"]["num_labels"] = len(model_p['obj_ids'])

        try:
            split_p = dataset_params.get_split_params(datasets_path, dataset, split = split)
        except ValueError:
            raise Exception("Wrong path or {} split does not exist in {}.".format(split, dataset))
        
        bpy.context.scene.world["category_id"] = 0
        bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", split_p['im_size'][0])
        bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", split_p['im_size'][1])

        # Collect camera and camera object
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data
        cam['loaded_resolution'] = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y 
        cam['loaded_intrinsics'] = cam_p['K'] # load default intrinsics from camera.json

        #only load all/selected objects here, use other modules for setting poses, e.g. camera.CameraSampler / object.ObjectPoseSampler
        if scene_id == -1:
            obj_ids = obj_ids if obj_ids else model_p['obj_ids']
            for obj_id in obj_ids:
                self._load_mesh(obj_id, model_p, mm2m=mm2m)
        # replicate scene: load scene objects, object poses, camera intrinsics and camera poses
        else:
            sc_gt = inout.load_scene_gt(split_p['scene_gt_tpath'].format(**{'scene_id':scene_id}))
            sc_camera = inout.load_json(split_p['scene_camera_tpath'].format(**{'scene_id':scene_id}))

            cm = CameraModule(self.config)

            for i, (cam_id, insts) in enumerate(sc_gt.items()):

                cam_K = np.array(sc_camera[str(cam_id)]['cam_K']).reshape(3,3)

                cam_H_m2c_ref = np.eye(4)
                cam_H_m2c_ref[:3,:3] = np.array(insts[0]['cam_R_m2c']).reshape(3,3) 
                cam_H_m2c_ref[:3, 3] = np.array(insts[0]['cam_t_m2c']).reshape(3) * mm2m

                if i == 0:
                    # define world = first camera
                    cam_H_m2w_ref = cam_H_m2c_ref.copy()
                    
                    for inst in insts:
                        cur_obj = self._load_mesh(inst['obj_id'], model_p, mm2m=mm2m)

                        cam_H_m2c = np.eye(4)
                        cam_H_m2c[:3,:3] = np.array(inst['cam_R_m2c']).reshape(3,3) 
                        cam_H_m2c[:3, 3] = np.array(inst['cam_t_m2c']).reshape(3) * mm2m

                        # world = camera @ i=0
                        cam_H_m2w = cam_H_m2c
                        print('-----------------------------')
                        print("Model: {}".format(cam_H_m2w))
                        print('-----------------------------')

                        cur_obj.matrix_world = Matrix(cam_H_m2w)
                        

                cam_H_c2w = np.dot(cam_H_m2w_ref, np.linalg.inv(cam_H_m2c_ref))

                print('-----------------------------')
                print("Cam: {}".format(cam_H_c2w))
                print('-----------------------------')

                config = {"location": [0,0,0], "rotation": list([0,0,0])}
                cm._add_cam_pose(Config(config), Matrix(cam_H_c2w), cam_K)


    def _try_duplicate_obj(self, model_path):
        """ If object with given model_path has already been loaded, duplicate this object

        :param model_path: model path of the new object
        :return: True if object was duplicated else False

        """
        for loaded_obj in bpy.context.selected_objects:
            if loaded_obj['model_path'] == model_path:
                print('duplicate obj: ', model_path)
                bpy.ops.object.duplicate({"object" : loaded_obj, "selected_objects" : [loaded_obj]})
                return True
        return False

    def _load_mesh(self, obj_id, model_p, mm2m=1):
        """ Loads or copies BOP mesh and sets category_id

        :param obj_id: The obj_id of the BOP Object (int)
        :param model_p: model parameters defined in dataset_params.py in bop_toolkit
        :param mm2m: "Specify whether to convert object scale from mm to meter"

        """

        model_path = model_p['model_tpath'].format(**{'obj_id': obj_id})
        
        duplicated = self._try_duplicate_obj(model_path)
        
        if not duplicated:
            print('load new mesh')
            bpy.ops.import_mesh.ply(filepath = model_path)

        cur_obj = bpy.context.selected_objects[-1]
        cur_obj.scale = Vector((mm2m, mm2m, mm2m))
        cur_obj['category_id'] = obj_id
        cur_obj['model_path'] = model_path

        mat = self._load_materials(cur_obj)
        self._link_col_node(mat)

        return cur_obj

    def _load_materials(self, cur_obj):
        """ Loads / defines materials, e.g. vertex colors 
        
        :param object: The object to use.

        return: material with vertex color (bpy.data.materials)
        """

        mat = cur_obj.data.materials.get("Material")
        
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name="Material")

        mat.use_nodes = True

        if cur_obj.data.materials:
            # assign to 1st material slot
            cur_obj.data.materials[0] = mat
        else:
            # no slots
            cur_obj.data.materials.append(mat)

        return mat

    def _link_col_node(self, mat):
        """Links a color attribute node to a Principled BSDF node 

        :param object: The material to use.
        """
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        attr_node = nodes.new(type='ShaderNodeAttribute')
        attr_node.attribute_name = 'Col'

        principled_node = nodes.get("Principled BSDF")

        links.new(attr_node.outputs['Color'], principled_node.inputs[0])
