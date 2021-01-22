import bpy

from src.utility.CameraUtility import CameraUtility
from src.utility.ItemWriter import ItemWriter
from src.writer.WriterInterface import WriterInterface


class CameraStateWriter(WriterInterface):
    """ Writes the state of all camera poses to a numpy file, if there was no hdf5 file to add them to.

    **Attributes per object**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - fov_x
          - The horizontal FOV.
          - float
        * - fov_y
          - The vertical FOV.
          - float
        * - half_fov_x
          - Half of the horizontal FOV.
          - float
        * - half_fov_y
          - Half of the vertical FOV.
          - float
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        self.object_writer = ItemWriter(self._get_attribute)

    def run(self):
        """ Collect camera and camera object and write them to a file."""
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data
        cam_pose = (cam, cam_ob)

        self.write_attributes_to_file(self.object_writer, [cam_pose], "campose_", "campose", ["id", "cam2world_matrix", "cam_K"])

    def _get_attribute(self, cam_pose, attribute_name):
        """ Returns the value of the requested attribute for the given object.

        :param cam_pose: The mesh object.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """
        cam, cam_ob = cam_pose

        if attribute_name == "fov_x":
            return cam.angle_x
        elif attribute_name == "fov_y":
            return cam.angle_y
        elif attribute_name == "shift_x":
            return cam.shift_x
        elif attribute_name == "shift_y":
            return cam.shift_y
        elif attribute_name == "half_fov_x":
            return cam.angle_x * 0.5
        elif attribute_name == "half_fov_y":
            return cam.angle_y * 0.5
        elif attribute_name == "cam_K":
            return [[x for x in c] for c in CameraUtility.get_intrinsics_as_K_matrix()]
        elif attribute_name == "cam2world_matrix":
            return super()._get_attribute(cam_ob, "matrix_world")
        else:
            return super()._get_attribute(cam_ob, attribute_name)
