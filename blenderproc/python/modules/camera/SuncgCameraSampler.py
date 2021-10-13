import bpy

from blenderproc.python.modules.camera.CameraSampler import CameraSampler
from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes
from blenderproc.python.sampler.SuncgPointInRoomSampler import SuncgPointInRoomSampler
from mathutils import Matrix

class SuncgCameraSampler(CameraSampler):
    """ Samples valid camera poses inside suncg rooms.

    Works as the standard camera sampler, except the following differences:
    - Always sets the x and y coordinate of the camera location to a value uniformly sampled inside a rooms bounding box
    - The configured z coordinate of the configured camera location is used as relative to the floor
    - All sampled camera locations need to lie straight above the room's floor to be valid
    
    See parent class CameraSampler for more details.

    """
    def __init__(self, config):
        CameraSampler.__init__(self, config)

    def run(self):
        self.point_sampler = SuncgPointInRoomSampler(convert_to_meshes(bpy.context.scene.objects))
        super().run()

    def _sample_pose(self, config):
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param config: The config object describing how to sample
        :return: True, if the sampled pose was valid
        """
        cam2world_matrix = super()._sample_pose(config)
        cam2world_matrix[:3,3], room_id = self.point_sampler.sample(height = cam2world_matrix[2,3])
        bpy.context.scene.camera["room_id"] = room_id
        return cam2world_matrix

    def _on_new_pose_added(self, cam2world_matrix: Matrix, frame: int):
        """ Inserts keyframe for room id corresponding to new camera poses.

        :param cam2world_matrix: The new camera pose.
        :param frame: The frame containing the new pose.
        """
        bpy.context.scene.camera.keyframe_insert(data_path='["room_id"]', frame=frame)
        super()._on_new_pose_added(cam2world_matrix, frame)
