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

        model_p = dataset_params.get_model_params(datasets_path, dataset, model_type='reconst')
        # camera_p = dataset_params.get_camera_params(datasets_path, dataset)
        split_p = dataset_params.get_split_params(datasets_path, dataset, 'test')


        # try scene_id in split_p['scene_ids']:
        sc_gt = inout.load_scene_gt(split_p['scene_gt_tpath'].format(**{'scene_id':scene_id}))
        sc_camera = inout.load_json(split_p['scene_camera_tpath'].format(**{'scene_id':scene_id}))

        cam_H_w2c = np.eye(4)
        cam_H_w2c[:3,:3] = np.array(sc_camera['1']['cam_R_w2c']).reshape(3,3) 
        cam_H_w2c[:3, 3] = np.array(sc_camera['1']['cam_t_w2c']).reshape(3) *0.01
        print(sc_gt.keys())
        for gt in sc_gt[1]:
           
            bpy.ops.import_mesh.ply(filepath=model_p['model_tpath'].format(**{'obj_id': gt['obj_id']}))
            
            cam_H_m2c = np.eye(4)
            cam_H_m2c[:3,:3] = np.array(gt['cam_R_m2c']).reshape(3,3) 
            cam_H_m2c[:3, 3] = np.array(gt['cam_t_m2c']).reshape(3) *0.01

            cam_H_m2w = np.dot(np.linalg.inv(cam_H_w2c), cam_H_m2c) #in [mm]

            cur_obj = bpy.context.selected_objects[-1]

            mat_H = Matrix.Identity(4)
            mat_H[0][0], mat_H[0][1], mat_H[0][2], mat_H[0][3] = cam_H_m2w[0,0], cam_H_m2w[0,1], cam_H_m2w[0,2], cam_H_m2w[0,3]
            mat_H[1][0], mat_H[1][1], mat_H[1][2], mat_H[1][3] = cam_H_m2w[1,0], cam_H_m2w[1,1], cam_H_m2w[1,2], cam_H_m2w[1,3]
            mat_H[2][0], mat_H[2][1], mat_H[2][2], mat_H[2][3] = cam_H_m2w[2,0], cam_H_m2w[2,1], cam_H_m2w[2,2], cam_H_m2w[2,3]
            mat_H[3][0], mat_H[3][1], mat_H[3][2], mat_H[3][3] = cam_H_m2w[3, 0], cam_H_m2w[3, 1], cam_H_m2w[3, 2], cam_H_m2w[3, 3]

            cur_obj.matrix_world = mat_H # m2w = c2w @ m2c
            cur_obj.scale = Vector((0.01,0.01,0.01))
            print(cur_obj.data.vertex_colors.keys())
            
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

            if cur_obj.data.vertex_colors:
                color_layer = cur_obj.data.vertex_colors["Col"]
                print(color_layer)

            # for m in cur_obj.material_slots:
            #     print(m)
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            attr_node = nodes.new(type='ShaderNodeAttribute')
            attr_node.attribute_name = 'Col'

            principled_node = nodes.get("Principled BSDF")
            principled_node.inputs[0]

            links.new(attr_node.outputs['Color'],principled_node.inputs[0])



    