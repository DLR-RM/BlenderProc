from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.loader.BopLoader import load_bop


class BopLoaderModule(LoaderInterface):
    """
    Loads the 3D models of any BOP dataset and allows replicating BOP scenes
    
    - Interfaces with the bob_toolkit, allows loading of train, val and test splits
    - Relative camera poses are loaded/computed with respect to a reference model
    - Sets real camera intrinsics

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cam_type
          - Camera type. If not defined, dataset-specific default camera type is used. Default value: ""
          - string
        * - source_frame
          - Can be used if the given positions and rotations are specified in frames different from the blender
            frame. Has to be a list of three strings. Example: ['X', '-Z', 'Y']: Point (1,2,3) will be transformed
            to (1, -3, 2). Default: ["X", "-Y", "-Z"]. " Available: ['X', 'Y', 'Z', '-X', '-Y', '-Z'].
          - list
        * - sys_paths
          - System paths to append.
          - list
        * - bop_dataset_path
          - Full path to a specific bop dataset e.g. /home/user/bop/tless.
          - string
        * - mm2m
          - Specify whether to convert poses and models to meters. Optional. Default: False.
          - bool
        * - split
          - Optionally, test or val split depending on BOP dataset. Optional. Default: test.
          - string
        * - scene_id
          - Optionally, specify BOP dataset scene to synthetically replicate. Default: -1 (no scene is replicated,
            only BOP Objects are loaded).
          - int
        * - sample_objects
          - Toggles object sampling from the specified dataset. Default: False.
          - boolean
        * - num_of_objs_to_sample
          - Amount of objects to sample from the specified dataset. If this amount is bigger than the dataset
            actually contains, then all objects will be loaded. 
          - int
        * - obj_instances_limit
          - Limits the amount of object copies when sampling. Default: -1 (no limit).
          - int
        * - obj_ids
          - List of object ids to load. Default: [] (all objects from the given BOP dataset if scene_id is not
            specified).
          - list
        * - model_type
          - Optionally, specify type of BOP model. Type: string. Default: "".  Available: [reconst, cad or eval].
          - string
        * - move_origin_to_x_y_plane
          - Move center of the object to the lower side of the object, this will not work when used in combination with
            pose estimation tasks! This is designed for the use-case where BOP objects are used as filler objects in
            the background. Default: False
          - bool
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        """ Load BOP data """
        sample_objects = self.config.get_bool("sample_objects", False)
        if sample_objects:
            num_of_objs_to_sample = self.config.get_int("num_of_objs_to_sample")
            obj_instances_limit = self.config.get_int("obj_instances_limit", -1)
        else:
            num_of_objs_to_sample = None
            obj_instances_limit = -1

        loaded_objects = load_bop(
            bop_dataset_path=self.config.get_string("bop_dataset_path"),
            temp_dir=self._temp_dir,
            sys_paths=self.config.get_list("sys_paths"),
            model_type=self.config.get_string("model_type", ""),
            cam_type=self.config.get_string("cam_type", ""),
            split=self.config.get_string("split", "test"),
            scene_id=self.config.get_int("scene_id", -1),
            obj_ids=self.config.get_list("obj_ids", []),
            sample_objects=sample_objects,
            num_of_objs_to_sample=num_of_objs_to_sample,
            obj_instances_limit=obj_instances_limit,
            move_origin_to_x_y_plane=self.config.get_bool("move_origin_to_x_y_plane", False),
            source_frame=self.config.get_list("source_frame", ["X", "-Y", "-Z"]),
            mm2m=self.config.get_bool("mm2m", False)
        )

        self._set_properties(loaded_objects)