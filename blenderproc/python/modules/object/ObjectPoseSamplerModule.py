from blenderproc.python.modules.main.Module import Module
from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects
from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes
from blenderproc.python.object.ObjectPoseSampler import sample_poses


class ObjectPoseSamplerModule(Module):
    """
    Samples positions and rotations of selected object inside the sampling volume while performing mesh and
    bounding box collision checks.

    Example 1: Sample poses (locations and rotations) for objects with a suctom property `sample_pose` set to True.

    .. code-block:: yaml

        {
          "module": "object.ObjectPoseSampler",
          "config":{
            "max_iterations": 1000,
            "objects_to_sample": {
              "provider": "getter.Entity",
              "condition": {
                "cp_sample_pose": True
              }
            },
            "pos_sampler":{
              "provider": "sampler.Uniform3d",
              "max": [5,5,5],
              "min": [-5,-5,-5]
            },
            "rot_sampler": {
              "provider": "sampler.Uniform3d",
              "max": [0,0,0],
              "min": [6.28,6.28,6.28]
            }
          }
        }

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - objects_to_sample
          - Here call an appropriate Provider (Getter) in order to select objects. Default: all mesh objects.
          - Provider
        * - objects_to_check_collisions
          - Here call an appropriate Provider (Getter) in order to select objects that you want to check collisions with. Default: all mesh objects.
          - Provider
        * - max_iterations
          - Amount of tries before giving up on an object and moving to the next one. Default: 1000.
          - int
        * - pos_sampler
          - Here call an appropriate Provider (Sampler) in order to sample position (XYZ 3d vector) for each object.
          - Provider
        * - rot_sampler
          - Here call an appropriate Provider (Sampler) in order to sample rotation (Euler angles 3d vector) for
            each object. 
          - Provider
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """
        Samples positions and rotations of selected object inside the sampling volume while performing mesh and
        bounding box collision checks in the following steps:
        1. While we have objects remaining and have not run out of tries - sample a point. 
        2. If no collisions are found keep the point.
        """
        objects_to_sample = self.config.get_list("objects_to_sample", get_all_blender_mesh_objects())
        objects_to_check_collisions = self.config.get_list("objects_to_check_collisions", get_all_blender_mesh_objects())
        max_tries = self.config.get_int("max_iterations", 1000)

        def sample_pose(obj: MeshObject):
            obj.set_location(self.config.get_vector3d("pos_sampler"))
            obj.set_rotation_euler(self.config.get_vector3d("rot_sampler"))

        sample_poses(
            objects_to_sample=convert_to_meshes(objects_to_sample),
            sample_pose_func=sample_pose,
            objects_to_check_collisions=convert_to_meshes(objects_to_check_collisions),
            max_tries=max_tries
        )
