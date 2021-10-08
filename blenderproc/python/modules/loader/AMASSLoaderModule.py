import os
import random

from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.utility.Utility import resolve_path, Utility, resolve_resource
from blenderproc.python.loader.AMASSLoader import load_AMASS


class AMASSLoaderModule(LoaderInterface):
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
          - string
        * - body_model_gender
          - The model gender, pose will represented using male, female or neutral body shape. Default: "".
            Available:[male, female, neutral]. If none is selected a random one is choosen.
          - string
        * - subject_id
          - Type of motion from which the pose should be extracted, this is dataset dependent parameter. Default: "".
            If left empty a random subject id is picked.
          - string
        * - sequence_id
          - Sequence id in the dataset, sequences are the motion recorded to represent certain action. Default: -1.
            If set to -1 a random sequence id is selected.
          - int
        * - frame_id
          - Frame id in a selected motion sequence. Default: -1. If none is selected a random one is picked
          - int
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)
        self._data_path = resolve_path(self.config.get_string("data_path", resolve_resource("AMASS")))
        # Body Model Specs
        self._used_body_model_gender = self.config.get_string("body_model_gender", random.choice(["male", "female", "neutral"]))
        # These numbers are based on a recommendation from the authors. refer to visualization tutorial from the
        # authors: https://github.com/nghorbani/amass/blob/master/notebooks/01-AMASS_Visualization.ipynb
        self._num_betas = 10  # number of body parameters
        self._num_dmpls = 8  # number of DMPL parameters
        # Pose Specs
        self._used_sub_dataset_id = self.config.get_string("sub_dataset_id")
        self._used_subject_id = self.config.get_string("subject_id", "")
        self._used_sequence_id = self.config.get_int("sequence_id", -1)
        self._used_frame_id = self.config.get_int("frame_id", -1)

    def run(self):
        """
        use the pose parameters to generate the mesh and loads it to the scene.
        """
        loaded_obj = load_AMASS(
            data_path=self._data_path,
            sub_dataset_id=self._used_sub_dataset_id,
            temp_dir=self._temp_dir,
            body_model_gender=self._used_body_model_gender,
            subject_id=self._used_subject_id,
            sequence_id=self._used_sequence_id,
            frame_id=self._used_frame_id,
            num_betas=self._num_betas,
            num_dmpls=self._num_dmpls
        )

        self._set_properties(loaded_obj)
