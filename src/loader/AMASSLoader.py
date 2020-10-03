import glob
import json
import os
import random
from datetime import datetime
import numpy as np
import shutil

import mathutils

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.LabelIdMapping import LabelIdMapping

import torch
from human_body_prior.body_model.body_model import BodyModel


class AMASSLoader(LoaderInterface):
    """
    AMASS is a large dataset of human motions. it unifies multiple datasets by fitting the SMPL body model to mocap (
    motion capture) markers. The dataset includes SMPL-H body shapes and poses as well as DMPL soft tissue motions
    parameters for every frame in every motion sequence for the sub datasets. any human pose recorded in these
    motions could be reconstructed using the following parameters: sub dataset identifier, sequence id, frame id and
    model gender which will represent the pose, these parameters specify the exact pose to be generated.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    Finally it sets all objects to have a category_id corresponding to the void class,
    so it wouldn't trigger an exception in the SegMapRenderer.

    Note: if this module is used with another loader that loads objects with semantic mapping, make sure the other
    module is loaded first in the config file.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "data_path", "The path to the AMASS Dataset folder in resources folder. Type: string. Default:
       'resources/AMASS'." "_used_sub_dataset_id", "Identifier for the sub dataset, the dataset which the human pose
       object should be extracted from. Type: srtring." "_used_body_model_gender", "The model gender,
       pose will represented using male, female or neutral body shape. Type: string." "_used_subject_id",
       "Type of motion from which the pose should be extracted, this is dataset dependent parameter. Type: int."
       "_used_sequence_id", "Sequence id in the dataset, sequences are the motion recorded to represent certain
       action. Type: int." "_used_frame_id", "Frame id in a selected motion sequence. Type: int."
    """

    # list of all possible supported mocap datasets: ['CMU', 'Transitions_mocap', 'MPI_Limits', 'SSM_synced',
    # 'TotalCapture', 'Eyes_Japan_Dataset', 'MPI_mosh', 'MPI_HDM05', 'HumanEva', 'ACCAD', 'EKUT', 'SFU', 'KIT',
    # 'H36M', 'TCD_handMocap', 'BML']

    # dictionary contains mocap dataset name and path to its sub folder within the main dataset
    supported_mocap_datasets = {}

    def __init__(self, config):
        LoaderInterface.__init__(self, config)
        self._data_path = Utility.resolve_path(self.config.get_string("data_path", "resources/AMASS"))
        # Body Model Specs
        self._used_body_model_gender = self.config.get_string("body_model_gender")
        self._num_betas = 10  # number of body parameters
        self._num_dmpls = 8  # number of DMPL parameters
        # Pose Specs
        self._used_sub_dataset_id = self.config.get_string("sub_dataset_id")
        self._used_subject_id = self.config.get_string("subject_id")
        self._used_sequence_id = self.config.get_string("sequence_id")
        self._used_frame_id = self.config.get_string("frame_id")
        # Get the currently supported mocap datasets by this loader
        taxonomy_file_path = os.path.join(self._data_path, "taxonomy.json")  # TODO: file maintaince responsibility
        AMASSLoader._get_supported_mocap_datasets(taxonomy_file_path, self._data_path)

    @staticmethod
    def _get_pose_coefficients(used_sub_dataset_id, used_body_model_gender, used_subject_id,
                               used_sequence_id, used_frame_id):
        """
        Get the pose parameters used to generate mesh object represents the pose
        :param used_sub_dataset_id: Identifier for the sub dataset, the dataset which the human pose object should be extracted from.
        :param used_body_model_gender: The model gender, pose will represented using male, female or neutral body shape. Type: string.
        :param used_subject_id: Type of motion from which the pose should be extracted, this is dataset dependent parameter
        :param used_frame_id: Frame id in a selected motion sequence.
        :return: body pose and shape parameters
        """
        # check if the sub_dataset is supported
        if used_sub_dataset_id in AMASSLoader.supported_mocap_datasets:
            # get  path from dictionsary
            sub_dataset_path = AMASSLoader.supported_mocap_datasets[used_sub_dataset_id]
            # concatenate path to specific
            subject_path = os.path.join(sub_dataset_path, used_subject_id)
            sequence_path = os.path.join(subject_path,
                                         "{:02d}".format(int(used_subject_id)) + "_" + "{:02d}".format(
                                             int(used_sequence_id)) + "_poses.npz")
            if os.path.exists(sequence_path):
                # load AMASS dataset sequence file which contains the coefficients for the whole motion sequence
                sequence_body_data = np.load(sequence_path)
                # get the number of supported frames
                no_of_frames_per_sequence = sequence_body_data['poses'].shape[0]
                if used_frame_id is None or "":
                    frame_id = random.randint(0, no_of_frames_per_sequence)  # pick a random id
                else:
                    frame_id = int(used_frame_id)
                # Extract Body Model coefficients
                if frame_id in range(0, no_of_frames_per_sequence):
                    # use GPU to accelerate mesh calculations
                    comp_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    # controls the global root orientation
                    root_orient = torch.Tensor(sequence_body_data['poses'][frame_id:frame_id + 1, :3]).to(comp_device)
                    # controls the body
                    pose_body = torch.Tensor(sequence_body_data['poses'][frame_id:frame_id + 1, 3:66]).to(comp_device)
                    # controls the finger articulation
                    # pose_hand = torch.Tensor(sequence_body_data['poses'][frame_id:frame_id+1, 66:]).to(comp_device)
                    # controls the body shape
                    betas = torch.Tensor(sequence_body_data['betas'][:10][np.newaxis]).to(comp_device)
                    # controls soft tissue dynamics
                    # dmpls = torch.Tensor(sequence_body_data['dmpls'][frame_id:frame_id+1]).to(comp_device)

                    return pose_body, betas
                else:
                    raise Exception(
                        "Requested frame id is beyond sequence range, for the selected sequence, chooose frame id "
                        "within the following range: [{}, {}]".format(
                            0, no_of_frames_per_sequence))

            else:
                raise Exception("Invalid sequence/subject category identifiers, please choose a valid one")

        else:
            raise Exception(
                "The requested mocap dataset is not yest supported, please choose anothe one from the following "
                "supported datasets: {}".format(
                    [key for key, value in AMASSLoader.supported_mocap_datasets.items()]))

    @staticmethod
    def _load_parametric_body_model(used_body_model_gender, num_betas, num_dmpls, data_path):
        """
        loads the parametric model SMPL+H based on the input parameters
        :param used_body_model_gender: The model gender, pose will represented using male, female or neutral body shape. Type: string.
        :param num_betas: Body shape parameters, used for BodyModel inistatiation
        :param num_dmpls: deformation parameters, used for BodyModel inistantiation
        :param data_path: path to the AMASS dataset root folder.
        :return: parametric model instance BodyModel and face mesh values
        """
        bm_path = os.path.join(data_path, 'body_models/smplh', used_body_model_gender, 'model.npz')  # body model
        dmpl_path = os.path.join(data_path, 'body_models/dmpls', used_body_model_gender,
                                 'model.npz')  # deformation model
        comp_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        body_model = BodyModel(bm_path=bm_path, num_betas=num_betas, num_dmpls=num_dmpls, path_dmpl=dmpl_path).to(
            comp_device)
        faces = body_model.f.detach().cpu().numpy()
        return body_model, faces

    @staticmethod
    def _get_supported_mocap_datasets(taxonomy_file_path, data_path):
        """
        get latest updated list from taxonomoy json file about the supported mocap datasets supported in the loader
        module and update.supported_mocap_datasets list :param taxonomy_file_path: path to taxomomy.json file which
        contains the supported datasets and their respective paths :param data_path: path to the AMASS dataset root
        folder :return: None.
        """
        if os.path.exists(taxonomy_file_path):
            with open(taxonomy_file_path, "r") as f:
                loaded_data = json.load(f)
                for block in loaded_data:
                    if "sub_data_id" in block:
                        sub_dataset_id = block["sub_data_id"]
                        AMASSLoader.supported_mocap_datasets[sub_dataset_id] = os.path.join(data_path, block["path"])
        else:
            raise Exception("The taxonomy file could not be found: {}".format(taxonomy_file_path))

    @staticmethod
    def _clean_up_temp_dir(data_path):
        """ Cleans up temporary generated poses directory """
        temp_dir_path = os.path.join(data_path, "generated_poses")
        if os.path.exists(temp_dir_path):
            shutil.rmtree(temp_dir_path)

    @staticmethod
    def _write_body_mesh_to_obj_file(body_represenstation, faces, data_path):
        """
        write the generated pose as obj file on the desk.
        :param body_represenstation: parameters generated from the BodyModel model which represent the obj pose and shape.
        :param faces: face parametric model which is used to generate the face mesh.
        :param data_path: path to the AMASS dataset root folder
        :return: path to generated obj file.
        """
        mesh_output_path = os.path.join(data_path, "generated_poses")
        if not os.path.exists(mesh_output_path):
            os.mkdir(mesh_output_path)
        starttime = datetime.now().replace(microsecond=0)
        # Generate temp objecet with name = timestamp
        obj_file_name = datetime.strftime(starttime, '%Y%m%d_%H%M') + ".obj"
        # Write to an .obj file
        outmesh_path = os.path.join(mesh_output_path, obj_file_name)
        with open(outmesh_path, 'w') as fp:
            for v in body_represenstation.v[0].detach().cpu().numpy():  # convert from tensor to numpy
                fp.write('v %f %f %f\n' % (v[0], v[1], v[2]))
            for f in faces + 1:  # Faces are 1-based, not 0-based in obj files
                fp.write('f %d %d %d\n' % (f[0], f[1], f[2]))
        return outmesh_path

    def run(self):
        """
        use the pose parameters to generate the mesh and loads it to the scene.
        """
        # selected_obj = self._files_with_fitting_ids
        pose_body, betas = AMASSLoader._get_pose_coefficients(self._used_sub_dataset_id,
                                                              self._used_body_model_gender,
                                                              self._used_subject_id, self._used_sequence_id,
                                                              self._used_frame_id)
        # load parametric Model
        body_model, faces = AMASSLoader._load_parametric_body_model(self._used_body_model_gender, self._num_betas,
                                                                    self._num_dmpls, self._data_path)

        # Generate Body representations using SMPL model
        body_repr = body_model(pose_body=pose_body, betas=betas)
        # Generate .obj file represents the selected pose
        generated_obj = AMASSLoader._write_body_mesh_to_obj_file(body_repr, faces, self._data_path)

        loaded_obj = Utility.import_objects(generated_obj)

        self._correct_materials(loaded_obj)

        self._set_properties(loaded_obj)

        if "void" in LabelIdMapping.label_id_map:  # Check if using an id map
            for obj in loaded_obj:
                obj['category_id'] = LabelIdMapping.label_id_map["void"]

        # clean generated files
        AMASSLoader._clean_up_temp_dir(self._data_path)

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

                # Create a principled node and set the default color
                principled_node = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
                # Define human skin tone colors
                principled_node.inputs["Base Color"].default_value = mathutils.Vector([141, 85, 36, 255]) / 255.0
                principled_node.inputs["Subsurface"].default_value = 0.2
                principled_node.inputs["Subsurface Color"].default_value = mathutils.Vector([141, 85, 36, 255]) / 255.0

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
