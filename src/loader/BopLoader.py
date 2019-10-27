import json
import os
from mathutils import Matrix, Vector, Euler
import math
import csv
import bpy
import numpy as np
from copy import deepcopy

from src.main.Module import Module
from src.utility.Utility import Utility
from src.utility.Config import Config
from src.camera.CameraModule import CameraModule
from bop_toolkit_lib import dataset_params, inout

class BopLoader(Module):
    """ Replicates a scene of any BOP dataset by loading 3D models and cameras in their gt poses
    
    - Interfaces with the bob_toolkit, allows loading of train, val and test splits
    - Relative cameras are loaded/computed with respect to a reference model

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "bop_dataset_path", "Full path to a specific bop dataset e.g. /home/user/bop/tless"
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        bop_dataset_path = self.config.get_string("bop_dataset_path")
        scene_id = self.config.get_int("scene_id")
        split = self.config.get_string("split", "test")
        model_type = self.config.get_string("model_type", "")
        mm2m = 0.001 if self.config.get_bool("mm2m") else 1

        datasets_path = os.path.dirname(bop_dataset_path)
        dataset = os.path.basename(bop_dataset_path)
        print("bob: {}, dataset_path: {}".format(bop_dataset_path, datasets_path))
        print("dataset: {}".format(dataset))

        model_p = dataset_params.get_model_params(datasets_path, dataset, model_type=model_type if model_type else None)
        camera_p = dataset_params.get_camera_params(datasets_path, dataset)

        try:
            split_p = dataset_params.get_split_params(datasets_path, dataset, split = split)
        except ValueError:
            raise Exception("Wrong path or {} split does not exist in {}.".format(split, dataset))

        sc_gt = inout.load_scene_gt(split_p['scene_gt_tpath'].format(**{'scene_id':scene_id}))
        sc_camera = inout.load_json(split_p['scene_camera_tpath'].format(**{'scene_id':scene_id}))

        bpy.context.scene.render.resolution_x = self.config.get_int("resolution_x", split_p['im_size'][0])
        bpy.context.scene.render.resolution_y = self.config.get_int("resolution_y", split_p['im_size'][1])
        #bpy.context.scene.render.pixel_aspect_x = self.config.get_float("pixel_aspect_x", 1) #split_p['im_size'][0] / split_p['im_size'][1])

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
                    
                    bpy.ops.import_mesh.ply(filepath=model_p['model_tpath'].format(**{'obj_id': inst['obj_id']}))
                    
                    cam_H_m2c = np.eye(4)
                    cam_H_m2c[:3,:3] = np.array(inst['cam_R_m2c']).reshape(3,3) 
                    cam_H_m2c[:3, 3] = np.array(inst['cam_t_m2c']).reshape(3) * mm2m

                    # world = camera @ i=0
                    cam_H_m2w = cam_H_m2c
                    print('-----------------------------')
                    print("Model: {}".format(cam_H_m2w))
                    print('-----------------------------')

                    cur_obj = bpy.context.selected_objects[-1]
                    cur_obj.matrix_world = Matrix(cam_H_m2w)
                    cur_obj.scale = Vector((mm2m,mm2m,mm2m))

                    mat = self._load_materials(cur_obj)
                    self._link_col_node(mat)

            cam_H_c2w = np.dot(cam_H_m2w_ref, np.linalg.inv(cam_H_m2c_ref))

            print('-----------------------------')
            print("Cam: {}".format(cam_H_c2w))
            print('-----------------------------')

            config = {"location": [0,0,0], "rotation": list([0,0,0])}
            cm._add_cam_pose(Config(config), Matrix(cam_H_c2w), cam_K)

    def _load_materials(self, cur_obj):
        """ Loads / defines materials, e.g. vertex colors 
        
        :param object: The object to use.
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

        # if cur_obj.data.vertex_colors:
        #     color_layer = cur_obj.data.vertex_colors["Col"]
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
