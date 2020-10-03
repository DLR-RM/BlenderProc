import glob
import json
import os
import random
import torch
import numpy as np

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.LabelIdMapping import LabelIdMapping

from human_body_prior.body_model.body_model import BodyModel


class AMASSLoader(LoaderInterface):
    """
    This loads an object from ShapeNet based on the given synset_id, which specifies the category of objects to use.
    From these objects one is randomly sampled and loaded.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    Finally it sets all objects to have a category_id corresponding to the void class, 
    so it wouldn't trigger an exception in the SegMapRenderer.

    Note: if this module is used with another loader that loads objects with semantic mapping, make sure the other module is loaded first in the config file.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "data_path", "The path to the ShapeNetCore.v2 folder. Type: string."
       "used_synset_id", "The synset id for example: '02691156', check the data_path folder for more ids. Type: int."
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

        self._data_path = Utility.resolve_path(self.config.get_string("data_path")) # AMASS folder
        self._used_sub_dataset_id = self.config.get_string("sub_dataset_id") # example: CMU
        self._used_body_model_gender = self.config.get_string("body_model_gender") # options:[male, female, neutral]
        self._used_subject_id = self.config.get_string("subject_id") # example: CMU/Subject 10: kick soccer ball
        self._used_sequence_id = self.config.get_string("sequence_id") # arbitrary sequence, the subject has 6 recorded motions, just pick one of them
        self._used_frame_id = self.config.get_string("frame_id") # arbitrary frame, if not selected, pick a randomly generated frame

        #this file lists the currently supported datasets and path to each sub_dataset_directory along some information about it,
        # BlenderPloc are responsible for this file and should host it and added to download script 
        taxonomy_file_path = os.path.join(self._data_path, "taxonomy.json")
        self._files_with_fitting_ids = AMASSLoader.get_files_with_ids(self._used_sub_dataset_id, self._used_body_model_gender, self._used_subject_id, self._used_sequence_id, self._used_frame_id, taxonomy_file_path, self._data_path)

    @staticmethod
    def _write_body_mesh_to_obj_file(data_path, body_represenstation, faces):
        mesh_output_path = os.path.join(data_path, "generated_poses")
        if not os.path.exists(mesh_output_path):
            os.mkdir(mesh_output_path)
        ## Write to an .obj file
        outmesh_path = os.path.join(mesh_output_path, './hello_smpl.obj')
        with open( outmesh_path, 'w') as fp:
            for v in body_represenstation.v[0].detach().cpu().numpy(): #convert from tensor to numpy
                fp.write( 'v %f %f %f\n' % ( v[0], v[1], v[2]) )
            for f in faces+1: # Faces are 1-based, not 0-based in obj files
                fp.write( 'f %d %d %d\n' %  (f[0], f[1], f[2]) )
        return outmesh_path

    @staticmethod
    def _extract_body_mesh_repr(sequence_path, used_body_model_gender, used_frame_id, data_path):
        """
        Returns obj file bath which represents the selected pose from the sun_dataset based on the user input of 
        """
        sequence_body_data = np.load(sequence_path) # body parameters for all frames in the sequence
        no_of_frames_per_sequence = sequence_body_data['poses'].shape[0] # get the number of supported frames
        if used_frame_id is None or "":            
            frame_id = random.randint(0, no_of_frames_per_sequence) # pick a random id
        else:
            frame_id = int(used_frame_id)

        comp_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        root_orient = torch.Tensor(sequence_body_data['poses'][frame_id:frame_id+1, :3]).to(comp_device) # controls the global root orientation
        pose_body = torch.Tensor(sequence_body_data['poses'][frame_id:frame_id+1, 3:66]).to(comp_device) # controls the body
        pose_hand = torch.Tensor(sequence_body_data['poses'][frame_id:frame_id+1, 66:]).to(comp_device) # controls the finger articulation
        betas = torch.Tensor(sequence_body_data['betas'][:10][np.newaxis]).to(comp_device) # controls the body shape
        dmpls = torch.Tensor(sequence_body_data['dmpls'][frame_id:frame_id+1]).to(comp_device) # controls soft tissue dynamics

        # TODO: to be fetched from the user
        num_betas = 10 # number of body parameters
        num_dmpls = 8 # number of DMPL parameters

        body_model, faces = AMASSLoader._load_parametric_body_model(data_path, used_body_model_gender, num_betas, num_dmpls)
        body_represenstation = body_model(pose_body=pose_body, betas=betas)
        outmesh_path = AMASSLoader._write_body_mesh_to_obj_file(data_path, body_represenstation, faces)
        
        return outmesh_path


    @staticmethod
    def get_files_with_ids(used_sub_dataset_id, used_body_model_gender, used_subject_id, used_sequence_id, used_frame_id, path_to_taxonomy_file, data_path):
        """
        Returns a list of a .obj file for the given synset_id
        :param used_synset_id: the id of the category something like: '02691156', see the data_path folder for more ids
        :param path_to_taxonomy_file: path to the taxonomy.json file, should be in the data_path, too
        :param data_path: path to the ShapeNetCore.v2 folder
        :return: list of .obj files, which are in the synset_id folder, based on the given taxonomy
        """
        if os.path.exists(path_to_taxonomy_file):
            
            with open(path_to_taxonomy_file, "r") as f:
                loaded_data = json.load(f)
                for block in loaded_data:
                    print("DEBUG", block)
                    if "sub_data_id" in block:
                        sub_dataset_id = block["sub_data_id"]
                        if sub_dataset_id == used_sub_dataset_id: #check if the sub_dataset is supported
                            sub_dataset_path = os.path.join(data_path, block["path"]) # concatenate path to specific subset
                            subject_path = os.path.join(sub_dataset_path, used_subject_id) # concatenate path to specific 
                            # concatenate the sequence id to path
                            
                            sequence_path = os.path.join(subject_path, "{:02d}".format(int(used_subject_id))+"_"+"{:02d}".format(int(used_sequence_id))+"_poses.npz")
                            print("DBG", sequence_path) # DBG

                            # get the path of the output mesh obj file
                            files = AMASSLoader._extract_body_mesh_repr(sequence_path, used_body_model_gender, used_frame_id, data_path)

                            

                            # run the pipleline to generate obj file, name it a meaniggul name
                            # return thr path to the generated object file
                            
            print("DEBUG",files)
            return files
        else:
            raise Exception("The taxonomy file could not be found: {}".format(path_to_taxonomy_file))

    

        
        
        

        # run the body data inside the model to calculate the body mesh
        # write the object file on the desk and return path to it
    @staticmethod
    def _load_parametric_body_model(data_path, used_body_model_gender, num_betas, num_dmpls):
        """
        Retunrs the parametric body model used to calculate the meshes of requested poses
        """
        bm_path = os.path.join(data_path, 'body_models/smplh', used_body_model_gender , 'model.npz') #body model
        dmpl_path = os.path.join(data_path, 'body_models/dmpls', used_body_model_gender, 'model.npz') #deformation model
        comp_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        body_model = BodyModel(bm_path=bm_path, num_betas=num_betas, num_dmpls=num_dmpls, path_dmpl=dmpl_path).to(comp_device)
        faces = body_model.f.detach().cpu().numpy()
        return body_model, faces







    def run(self):
        """
        Uses the loaded .obj files and picks one randomly and loads it
        """
        selected_obj = self._files_with_fitting_ids
        loaded_obj = Utility.import_objects(selected_obj)

        self._correct_materials(loaded_obj)

        self._set_properties(loaded_obj)

        if "void" in LabelIdMapping.label_id_map:  # Check if using an id map
            for obj in loaded_obj:
                obj['category_id'] = LabelIdMapping.label_id_map["void"]

    def _correct_materials(self, objects):
        """
        If the used material contains an alpha texture, the alpha texture has to be flipped to be correct
        :param objects, objects where the material maybe wrong
        """

        for obj in objects:
            for mat_slot in obj.material_slots:
                material = mat_slot.material
                nodes = material.node_tree.nodes
                links = material.node_tree.links
                texture_nodes = Utility.get_nodes_with_type(nodes, "ShaderNodeTexImage")
                if texture_nodes and len(texture_nodes) > 1:
                    principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                    # find the image texture node which is connect to alpha
                    node_connected_to_the_alpha = None
                    for node_links in principled_bsdf.inputs["Alpha"].links:
                        if "ShaderNodeTexImage" in node_links.from_node.bl_idname:
                            node_connected_to_the_alpha = node_links.from_node
                    # if a node was found which is connected to the alpha node, add an invert between the two
                    if node_connected_to_the_alpha is not None:
                        invert_node = nodes.new("ShaderNodeInvert")
                        invert_node.inputs["Fac"].default_value = 1.0
                        Utility.insert_node_instead_existing_link(links, node_connected_to_the_alpha.outputs["Color"],
                                                                  invert_node.inputs["Color"],
                                                                  invert_node.outputs["Color"],
                                                                  principled_bsdf.inputs["Alpha"])
