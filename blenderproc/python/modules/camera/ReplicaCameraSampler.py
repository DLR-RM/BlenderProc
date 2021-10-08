import os

from blenderproc.python.modules.camera.CameraSampler import CameraSampler
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.utility.Utility import resolve_path, Utility, resolve_resource
from blenderproc.python.sampler.ReplicaPointInRoomSampler import ReplicaPointInRoomSampler
import bpy

class ReplicaCameraSampler(CameraSampler):
    """
    Samples valid camera poses inside replica rooms.

    Works as the standard camera sampler, except the following differences:
    - Always sets the x and y coordinate of the camera location to a value uniformly sampled inside of a room's \
      bounding box
    - The configured z coordinate of the configured camera location is used as relative to the floor
    - All sampled camera locations need to lie straight above the room's floor to be valid
    - Using the scene coverage/interestingness score in the ReplicaCameraSampler does not make much sense, as the \
      3D mesh is not split into individual objects.

    See parent class CameraSampler for more details.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - is_replica_object
          - Whether it's a Replica object. Default: False.
          - bool
        * - height_list_path
          - Path to height list.
          - string
        * - data_set_name
          - Dataset name in case is_replica_object is set to false.
          - string
    """

    def __init__(self, config):
        CameraSampler.__init__(self, config)

    def run(self):
        # Load the height levels of this scene
        if not self.config.get_bool('is_replica_object', False):
            file_path = self.config.get_string('height_list_path')
        else:
            folder_path = os.path.join('replica', 'height_levels', self.config.get_string('data_set_name'))
            file_path = resolve_resource(os.path.join(folder_path, 'height_list_values.txt'))

        if 'mesh' in bpy.data.objects:
            mesh = MeshObject(bpy.data.objects['mesh'])
        else:
            raise Exception("Mesh object is not defined!")

        # Find floor object
        if 'floor' in bpy.data.objects:
            floor_object = MeshObject(bpy.data.objects['floor'])
        else:
            raise Exception("No floor object is defined!")

        self.point_sampler = ReplicaPointInRoomSampler(mesh, floor_object, file_path)
        super().run()

    def _sample_pose(self, config):
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param config: The config object describing how to sample
        :return: True, if the sampled pose was valid
        """
        cam2world_matrix = super()._sample_pose(config)
        cam2world_matrix[:3,3] = self.point_sampler.sample(height = cam2world_matrix[2,3])
        return cam2world_matrix