import json
import os
import random
from datetime import datetime
import numpy as np

import mathutils

from src.loader.LoaderInterface import LoaderInterface
from src.utility.Utility import Utility
from src.utility.LabelIdMapping import LabelIdMapping

import torch
from human_body_prior.body_model.body_model import BodyModel


class AMASSLoader(LoaderInterface):
    """
    AMASS is a large database of human motion unifying 15 different optical marker-based motion capture datasets by representing them within a common framework and parameterization. All of the mocap data is convereted into realistic 3D human meshes represented by a rigged body model called SMPL, which provides a standard skeletal representation as well as a fully rigged surface mesh. Warning: Only one part of the AMASS database is currently supported by the loader! Please refer to the AMASSLoader example for more information about the currently supported datasets.

    Any human pose recorded in these motions could be reconstructed using the following parameters: `"sub_dataset_identifier"`, `"sequence id"`, `"frame id"` and `"model gender"` which will represent the pose, these parameters specify the exact pose to be generated based on the selected mocap dataset and motion category recorded in this dataset.

    As for all loaders it is possible to add custom properties to the loaded object, for that use add_properties.

    Finally it sets all objects to have a category_id corresponding to the void class,
    so it wouldn't trigger an exception in the SegMapRenderer.

    Note: if this module is used with another loader that loads objects with semantic mapping, make sure the other
    module is loaded first in the config file.

    Example 1: generate a pose of a human kicking a ball (male model). There are different categories recorded in the mocap datasets inside of the AMASS database, for the CMU dataset we can see that the category number `10` contains multiple trials of humans kicking a ball.

    .. code-block:: yaml

        {
            "module": "loader.AMASSLoader",
            "config": {
            "data_path": "<args:0>",
            "sub_dataset_id": "CMU",
            "body_model_gender": "male",
            "subject_id": "10",
            "sequence_id": "1",
            "frame_id": "600",
          },
        }

    Example 2: generate a pose of human picking up golf ball (female model). Here we choose from the CMU dataset the subject number 64, which contains multiple trials of a human playing golf, if frame_id is not specified (by removing it from the configuration arguments), a random frame will be chosen from the motion trial.

    .. code-block:: yaml

        {
            "module": "loader.AMASSLoader",
            "config": {
            "data_path": "<args:0>",
            "sub_dataset_id": "CMU",
            "body_model_gender": "female",
            "subject_id": "64",
            "sequence_id": "27",
          },
        }

    **Configuration**:

    .. list-table::
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_path
          - The path to the AMASS Dataset folder in resources folder. Default: 'resources/AMASS'.
          - string
        * - sub_dataset_id
          - Identifier for the sub dataset, the dataset which the human pose object should be extracted from.
            Available: ['CMU', 'Transitions_mocap', 'MPI_Limits', 'SSM_synced', 'TotalCapture',
            'Eyes_Japan_Dataset', 'MPI_mosh', 'MPI_HDM05', 'HumanEva', 'ACCAD', 'EKUT', 'SFU', 'KIT', 'H36M', 'TCD_handMocap', 'BML']
          - srtring
        * - body_model_gender
          - The model gender, pose will represented using male, female or neutral body shape. Available:[male,
            female, neutral]
          - string
        * - subject_id
          - Type of motion from which the pose should be extracted, this is dataset dependent parameter.
          - int
        * - sequence_id
          - Sequence id in the dataset, sequences are the motion recorded to represent certain action.
          - int
        * - frame_id
          - Frame id in a selected motion sequence.
          - int
    """

    # dictionary contains mocap dataset name and path to its sub folder within the main dataset, dictionary will
    # be filled from taxonomy.json file which indicates the supported datastests
    supported_mocap_datasets = {}

    # hex values for human skin tone to sample from
    human_skin_colors = ['2D221E', '3C2E28', '4B3932', '5A453C', '695046', '785C50', '87675A', '967264', 'A57E6E',
                         'B48A78', 'C39582', 'D2A18C', 'E1AC96', 'F0B8A0', 'FFC3AA', 'FFCEB4', 'FFDABE', 'FFE5C8']

    def __init__(self, config):
        LoaderInterface.__init__(self, config)
        self._data_path = Utility.resolve_path(
            self.config.get_string("data_path", os.path.join("resources", "AMASS")))
        # Body Model Specs
        self._used_body_model_gender = self.config.get_string(
            "body_model_gender")
        # These numbers are based on a recommendation from the authors. refer to visualization tutorial from the authors: https://github.com/nghorbani/amass/blob/master/notebooks/01-AMASS_Visualization.ipynb
        self._num_betas = 10  # number of body parameters
        self._num_dmpls = 8  # number of DMPL parameters
        # Pose Specs
        self._used_sub_dataset_id = self.config.get_string("sub_dataset_id")
        self._used_subject_id = self.config.get_string("subject_id")
        self._used_sequence_id = self.config.get_string("sequence_id")
        self._used_frame_id = self.config.get_string("frame_id", "")
        # Get the currently supported mocap datasets by this loader
        taxonomy_file_path = os.path.join(self._data_path, "taxonomy.json")
        AMASSLoader._get_supported_mocap_datasets(
            taxonomy_file_path, self._data_path)

    def _get_pose_parameters(self):
        """ Extract pose and shape parameters corresponding to the requested pose from the database to be processed by the parametric model

        :returns: tuple of arrays contains the parameters. Type: tuple
        """
        # check if the sub_dataset is supported
        if self._used_sub_dataset_id in AMASSLoader.supported_mocap_datasets:
            # get  path from dictionsary
            sub_dataset_path = AMASSLoader.supported_mocap_datasets[self._used_sub_dataset_id]
            # concatenate path to specific
            subject_path = os.path.join(
                sub_dataset_path, self._used_subject_id)
            sequence_path = os.path.join(subject_path,
                                         "{:02d}".format(int(self._used_subject_id)) + "_" + "{:02d}".format(
                                             int(self._used_sequence_id)) + "_poses.npz")
            if os.path.exists(sequence_path):
                # load AMASS dataset sequence file which contains the coefficients for the whole motion sequence
                sequence_body_data = np.load(sequence_path)
                # get the number of supported frames
                no_of_frames_per_sequence = sequence_body_data['poses'].shape[0]
                if self._used_frame_id == "":
                    frame_id = random.randint(
                        0, no_of_frames_per_sequence)  # pick a random id
                else:
                    frame_id = int(self._used_frame_id)
                # Extract Body Model coefficients
                if frame_id in range(0, no_of_frames_per_sequence):
                    # use GPU to accelerate mesh calculations
                    comp_device = torch.device(
                        "cuda" if torch.cuda.is_available() else "cpu")
                    # parameters that control the body pose
                    # refer to http://files.is.tue.mpg.de/black/papers/amass.pdf, Section 3.1 for more information about the parameter representation and the below chosen values
                    pose_body = torch.Tensor(
                        sequence_body_data['poses'][frame_id:frame_id + 1, 3:66]).to(comp_device)
                    # parameters that control the body shape
                    betas = torch.Tensor(
                        sequence_body_data['betas'][:self._num_betas][np.newaxis]).to(comp_device)
                    return pose_body, betas
                else:
                    raise Exception(
                        "Requested frame id is beyond sequence range, for the selected sequence, chooose frame id "
                        "within the following range: [{}, {}]".format(0, no_of_frames_per_sequence))

            else:
                raise Exception(
                    "Invalid sequence/subject category identifiers, please choose a valid one")

        else:
            raise Exception(
                "The requested mocap dataset is not yest supported, please choose anothe one from the following "
                "supported datasets: {}".format(
                    [key for key, value in AMASSLoader.supported_mocap_datasets.items()]))

    def _load_parametric_body_model(self):
        """ loads the parametric model that is used to generate the mesh object

        :return:  parametric model. Type: tuple.
        """
        bm_path = os.path.join(self._data_path, 'body_models', 'smplh',
                               self._used_body_model_gender, 'model.npz')  # body model
        dmpl_path = os.path.join(self._data_path, 'body_models', 'dmpls',
                                 self._used_body_model_gender, 'model.npz')  # deformation model
        if not os.path.exists(bm_path) or not os.path.exists(dmpl_path):
            raise Exception(
                "Parametric Body model doesn't exist, please follow download instructions section in AMASS Example")
        comp_device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        body_model = BodyModel(bm_path=bm_path, num_betas=self._num_betas, num_dmpls=self._num_dmpls, path_dmpl=dmpl_path).to(
            comp_device)
        faces = body_model.f.detach().cpu().numpy()
        return body_model, faces

    @staticmethod
    def _get_supported_mocap_datasets(taxonomy_file_path, data_path):
        """ get latest updated list from taxonomoy json file about the supported mocap datasets supported in the loader module and update.supported_mocap_datasets list

        :param taxonomy_file_path: path to taxomomy.json file which contains the supported datasets and their respective paths. Type: string.
        :param data_path: path to the AMASS dataset root folder. Type: string.
        :return: None.
        """
        if os.path.exists(taxonomy_file_path):
            with open(taxonomy_file_path, "r") as f:
                loaded_data = json.load(f)
                for block in loaded_data:
                    if "sub_data_id" in block:
                        sub_dataset_id = block["sub_data_id"]
                        AMASSLoader.supported_mocap_datasets[sub_dataset_id] = os.path.join(
                            data_path, block["path"])
        else:
            raise Exception(
                "The taxonomy file could not be found: {}".format(taxonomy_file_path))

    def _write_body_mesh_to_obj_file(self, body_represenstation, faces):
        """ write the generated pose as obj file on the desk.

        :param body_represenstation: parameters generated from the BodyModel model which represent the obj pose and shape. Type: torch.Tensor
        :param faces: face parametric model which is used to generate the face mesh. Type: numpy.array
        :return: path to generated obj file. Type: string.
        """
        # Generate temp object with name = timestamp
        starttime = datetime.now().replace(microsecond=0)
        obj_file_name = datetime.strftime(starttime, '%Y%m%d_%H%M') + ".obj"
        # Write to an .obj file
        outmesh_path = os.path.join(self._temp_dir, obj_file_name)
        with open(outmesh_path, 'w') as fp:
            fp.write("".join(['v {:f} {:f} {:f}\n'.format(v[0], v[1], v[2])
                              for v in body_represenstation.v[0].detach().cpu().numpy()]))
            fp.write("".join(['f {} {} {}\n'.format(
                f[0], f[1], f[2]) for f in faces + 1]))
        return outmesh_path

    def run(self):
        """
        use the pose parameters to generate the mesh and loads it to the scene.
        """
        # selected_obj = self._files_with_fitting_ids
        pose_body, betas = self._get_pose_parameters()
        # load parametric Model
        body_model, faces = self._load_parametric_body_model()
        # Generate Body representations using SMPL model
        body_repr = body_model(pose_body=pose_body, betas=betas)
        # Generate .obj file represents the selected pose
        generated_obj = self._write_body_mesh_to_obj_file(body_repr, faces)

        loaded_obj = Utility.import_objects(generated_obj)

        self._correct_materials(loaded_obj)

        self._set_properties(loaded_obj)
        # set the shading mode explicitly to smooth
        self.change_shading_mode(loaded_obj, "SMOOTH")

        if "void" in LabelIdMapping.label_id_map:  # Check if using an id map
            for obj in loaded_obj:
                obj['category_id'] = LabelIdMapping.label_id_map["void"]

    def _correct_materials(self, objects):
        """ If the used material contains an alpha texture, the alpha texture has to be flipped to be correct

        :param objects: objects where the material maybe wrong. Type: bpy.types.Object.
        """

        for obj in objects:
            for mat_slot in obj.material_slots:
                material = mat_slot.material
                nodes = material.node_tree.nodes
                links = material.node_tree.links

                # Create a principled node and set the default color
                principled_bsdf = Utility.get_the_one_node_with_type(
                    nodes, "BsdfPrincipled")
                # Pick random skin color value
                skin_tone_hex = np.random.choice(AMASSLoader.human_skin_colors)
                skin_tone_rgb = list(
                    int(skin_tone_hex[i:i+2], 16) for i in (0, 2, 4))
                principled_bsdf.inputs["Base Color"].default_value = mathutils.Vector(
                    [*skin_tone_rgb, 255]) / 255.0
                principled_bsdf.inputs["Subsurface"].default_value = 0.2
                principled_bsdf.inputs["Subsurface Color"].default_value = mathutils.Vector(
                    [*skin_tone_rgb, 255]) / 255.0

                texture_nodes = Utility.get_nodes_with_type(
                    nodes, "ShaderNodeTexImage")
                if texture_nodes and len(texture_nodes) > 1:
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
