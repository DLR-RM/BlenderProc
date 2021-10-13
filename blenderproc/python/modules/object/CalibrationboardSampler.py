import bpy

from blenderproc.python.modules.main.Module import Module
from mathutils import Vector
import bpy_extras


class CalibrationboardSampler(Module):
    """
    Samples poses of a given calibration board across the camera view.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - board_name
          - Name of the chess board object.
          - string
        * - corner_coords
          - A list of coordinates in the local coordinates system of the chess board, that should always remain
            visible.
          - list
        * - small_step_size
          - The smaller step size to move the board outside of the camera view. A smaller step size is used here to
            also get poses at the border of the camera view. Default: 0.1
          - float
        * - big_step_size
          - The bigger step size to move the board inside of the camera view. A bigger step size is used here to not
            get too many similar poses. Default: 0.2
          - float
        * - x_min
          - Min. boundary of sampling space along x-axis. Default: -5
          - float
        * - x_max
          - Max. boundary of sampling space along y-axis. Default: 5
          - float
        * - y_min
          - Min. boundary of sampling space along x-axis. Default: -5
          - float
        * - y_max
          - Max. boundary of sampling space along y-axis. Default: 5
          - float
        * - z_planes
          - A list of z-planes on which poses should be sampled. Default: [-1, -2, -3]
          - list
        * - rot_sampler
          - Here call an appropriate Provider (Sampler) in order to sample rotation (Euler angles 3d vector) for the
            chess board.
          - Provider
    """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """
        Samples goes over different chess board poses and persists them if all specified corners are inside the camera view.
        """
        # Find chess board
        obj = bpy.context.scene.objects[self.config.get_string("board_name")]

        # Retrieve points that should always be in the camera view
        corners = self.config.get_list("corner_coords", [-1, -2, -3])
        for i in range(len(corners)):
            corners[i] = Vector(corners[i])

        # Initialize search area and step sizes
        frame = 0
        small_step = self.config.get_float("small_step_size", 0.1)
        big_step = self.config.get_float("big_step_size", 0.2)
        next_step_y = small_step
        next_step_x = small_step

        x_min = self.config.get_float("x_min", -5)
        x_max = self.config.get_float("x_max", 5)
        y_min = self.config.get_float("y_min", -5)
        y_max = self.config.get_float("y_max", 5)

        # Go over all z-planes
        for z in self.config.get_list("z_planes", [-1, -2, -3]):
            # Do the following two times once starting from (x_min, y_min) and once from (x_max, y_max). In this way we get poses at all borders of the image
            for dir in [1, -1]:
                # Step along the x-axis
                x = x_min * dir
                while x * dir < x_max:
                    # Step along the y-axis
                    y = y_min * dir
                    while y * dir < y_max:
                        # Set chess board location and sampler rotation
                        obj.location = [x, y, z]
                        obj.rotation_euler = self.config.get_vector3d("rot_sampler")
                        bpy.context.view_layer.update()

                        # Check that all specified points are inside the camera view
                        valid = True
                        for corner in corners:
                            point = obj.matrix_world @ corner
                            point2d_blender = bpy_extras.object_utils.world_to_camera_view(bpy.context.scene, bpy.context.scene.camera, point)

                            if not (0 < point2d_blender[0] < 1 and 0 < point2d_blender[1] < 1):
                                valid = False
                                break

                        if valid:
                            # Switch to big step size if we are inside the camera view
                            next_step_x = big_step * abs(z)
                            next_step_y = big_step * abs(z)

                            # Persist key frame
                            obj.keyframe_insert(data_path='location', frame=frame)
                            obj.keyframe_insert(data_path='rotation_euler', frame=frame)

                            frame += 1

                        # Do one y step
                        y += next_step_y * dir
                        next_step_y = small_step

                    # Do one x step
                    x += next_step_x * dir
                    next_step_x = small_step

        # Set max frames
        bpy.context.scene.frame_end = frame
