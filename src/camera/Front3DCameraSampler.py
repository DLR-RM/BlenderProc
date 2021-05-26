from src.camera.CameraSamplerModule import CameraSamplerModule
from src.utility.sampler.Front3DPointInRoomSampler import Front3DPointInRoomSampler


class Front3DCameraSampler(CameraSamplerModule):
    """
    This Camera Sampler is similar to how the SuncgCameraSampler works.

    It first searches for rooms, by using the different floors, which are used in each room.
    It then counts the amount of 3D-Future objects on this particular floor, to check if this room is interesting
    for creating cameras or not. The amount of needed objects can be changed via the config.
    If the amount is set to 0, all rooms will have cameras, even if these rooms are empty.

    The Front3D Loader provides information for using the min_interesting_score option.
    Furthermore, it supports the no_background: True option, which is useful as the 3D-Front dataset has no windows
    or doors to the outside world, which then leads to the background appearing in this shots, if not activated.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - amount_of_objects_needed_per_room
          - The amount of objects needed per room, so that cameras are sampled in it. This avoids that cameras are 
             sampled in empty rooms. Default: 2
          - int
    """

    def __init__(self, config):
        CameraSamplerModule.__init__(self, config)

    def run(self):
        self.point_sampler = Front3DPointInRoomSampler()
        super().run()

    def _sample_pose(self):
        """ Samples a new camera pose, sets the parameters of the given camera object accordingly and validates it.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: The config object describing how to sample
        :return: True, if the sampled pose was valid
        """
        cam2world_matrix = super()._sample_pose()
        cam2world_matrix.translation = self.point_sampler.sample(cam2world_matrix.translation[2])
        return cam2world_matrix