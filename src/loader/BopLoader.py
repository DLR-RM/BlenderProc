import json
import os
from mathutils import Matrix, Vector, Euler
import math
import csv
import bpy
import numpy as np

from src.main.Module import Module
from src.utility.Utility import Utility
from bop_toolkit_lib import dataset_params, inout

class BopLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """TODO: Load Bop toolkit params
        gt.json, info.json
        1. render test scenes and compare
        2. render random poses in params range
        3. render in front of random backgrounds
        
        """

        bop_dataset_path = self.config.get_string("datasets_path")
        scene_id = int(self.config.get_string("scene_id"))
        datasets_path = os.path.dirname(bop_dataset_path)
        dataset = os.path.basename(bop_dataset_path)
        print(bop_dataset_path)
        print(dataset)

        model_p = dataset_params.get_model_params(datasets_path, dataset)
        # camera_p = dataset_params.get_camera_params(datasets_path, dataset)
        split_p = dataset_params.get_split_params(datasets_path, dataset, 'test')


        # try scene_id in split_p['scene_ids']:
        sc_gt = inout.load_scene_gt(split_p['scene_gt_tpath'].format(**{'scene_id':scene_id}))
        sc_camera = inout.load_json(split_p['scene_camera_tpath'].format(**{'scene_id':scene_id}))
        cam_R_w2c = np.array(sc_camera['1']['cam_R_w2c']).reshape(3,3)
        cam_t_w2c = np.array(sc_camera['1']['cam_t_w2c']).reshape(3)
        cam_H_w2c = np.eye(4)
        cam_H_w2c[:3,:3] = cam_R_w2c 
        cam_H_w2c[:3, 3] = cam_t_w2c
        print(sc_gt.keys())
        print(cam_H_w2c)
        trafos = []
        for gt in sc_gt[1]:
            obj_id = gt['obj_id']
            
            bpy.ops.import_mesh.ply(filepath=model_p['model_tpath'].format(**{'obj_id':obj_id}))
            cam_R_m2c = np.array(gt['cam_R_m2c']).reshape(3,3)
            cam_t_m2c = np.array(gt['cam_t_m2c']).reshape(3)
            cam_H_m2c = np.eye(4)
            cam_H_m2c[:3,:3] = cam_R_m2c 
            cam_H_m2c[:3, 3] = cam_t_m2c


            cam_H_c2m = cam_H_m2c.copy()
            cam_H_c2m[:3,:3] = -cam_H_m2c[:3,:3].T
            cam_H_c2m[:3, 3] = -np.dot(cam_H_m2c[:3,:3].T, cam_H_m2c[:3, 3])

            cam_H_w2m = np.dot(cam_H_w2c, cam_H_c2m) #in [mm]
            # scale = np.eye(4) * 0.001
            # cam_H_w2m[:3,3] = cam_H_w2m[:3,3] * 0.001
            print(cam_H_w2m)
            # for cur_obj in bpy.context.selected_objects:
            #     print(np.dot(cur_obj.matrix_world, np.linalg.inv(cam_H_w2m)))
            #     cur_obj.matrix_world = np.dot(cur_obj.matrix_world, np.linalg.inv(cam_H_w2m))
            #     cur_obj.scale = np.array([0.01,0.01,0.01])
            trafos.append(cam_H_w2m)
        
        # Create 
        mat_rot = Matrix.Rotation(math.radians(90.0), 4, 'X')
        mat_trans = Matrix.Translation(Vector((1.0, 2.0, 3.0)))
        mat_sca = Matrix.Scale(1.0, 4)
        print(mat_trans)
        print(mat_sca)

        for cam_H_w2m, object in zip(trafos,bpy.context.selected_objects):
            print(object.matrix_world)
            mat_H = Matrix.Identity(4)
            # object.scale= Vector((0.01,0.01,0.01))
            mat_H[0][0], mat_H[0][1], mat_H[0][2], mat_H[0][3] = cam_H_w2m[0,0], cam_H_w2m[0,1], cam_H_w2m[0,2], cam_H_w2m[0,3]
            mat_H[1][0], mat_H[1][1], mat_H[1][2], mat_H[1][3] = cam_H_w2m[1,0], cam_H_w2m[1,1], cam_H_w2m[1,2], cam_H_w2m[1,3]
            mat_H[2][0], mat_H[2][1], mat_H[2][2], mat_H[2][3] = cam_H_w2m[2,0], cam_H_w2m[2,1], cam_H_w2m[2,2], cam_H_w2m[2,3]
            mat_H[3][0], mat_H[3][1], mat_H[3][2], mat_H[3][3] = cam_H_w2m[3, 0], cam_H_w2m[3, 1], cam_H_w2m[3, 2], cam_H_w2m[3,3]
            print(mat_H)
            transform = mat_H
            object.matrix_world @= cam_R_m2c



    