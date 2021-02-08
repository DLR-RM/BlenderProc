import bpy
import numpy as np
from mathutils import Matrix

class CameraUtility:

    @staticmethod
    def add_camera_pose(cam2world_matrix, frame=None):
        """ Sets a new camera pose to a new or existing frame

        :param cam2world_matrix: The transformation matrix from camera to world coordinate system
        :param frame: Optional, the frame to set the camera pose to.
        :return: The frame to which the pose has been set.
        """
        if not isinstance(cam2world_matrix, Matrix):
            cam2world_matrix = Matrix(cam2world_matrix)

        # Set cam2world_matrix
        cam_ob = bpy.context.scene.camera
        cam_ob.matrix_world = cam2world_matrix

        # Add new frame if no frame is given
        if frame is None:
            frame = bpy.context.scene.frame_end
        if bpy.context.scene.frame_end < frame + 1:
            bpy.context.scene.frame_end = frame + 1

        # Persist camera pose
        cam_ob.keyframe_insert(data_path='location', frame=frame)
        cam_ob.keyframe_insert(data_path='rotation_euler', frame=frame)

        return frame

    @staticmethod
    def rotation_from_forward_vec(forward_vec, up_axis='Y'):
        """ Returns a camera rotation matrix for the given forward vector and up axis

        :param forward_vec: The forward vector which specifies the direction the camera should look.
        :param up_axis: The up axis, usually Y.
        :return: The corresponding rotation matrix.
        """
        return forward_vec.to_track_quat('-Z', up_axis).to_matrix()

    @staticmethod
    def set_intrinsics_from_blender_params(lens, image_width, image_height, clip_start=0.1, clip_end=1000, pixel_aspect_x=1, pixel_aspect_y=1, shift_x=0, shift_y=0, lens_unit="MILLIMETERS"):
        """ Sets the camera intrinsics using blenders represenation.

        :param lens: Either the focal length in millimeters or the FOV in radians, depending on the given lens_unit.
        :param image_width: The image width in pixels.
        :param image_height: The image height in pixels.
        :param clip_start: Clipping start.
        :param clip_end: Clipping end.
        :param pixel_aspect_x: The pixel aspect ratio along x.
        :param pixel_aspect_y: The pixel aspect ratio along y.
        :param shift_x: The shift in x direction.
        :param shift_y: The shift in y direction.
        :param lens_unit: Either FOV or MILLIMETERS depending on whether the lens is defined as focal length in millimeters or as FOV in radians.
        """
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        # Set focal length
        if lens_unit == 'MILLIMETERS':
            cam.lens_unit = lens_unit
            if lens < 1:
                raise Exception("The focal length is smaller than 1mm which is not allowed in blender: " + str(lens))
            cam.lens = lens
        elif lens_unit == "FOV":
            cam.lens_unit = lens_unit
            cam.angle = lens
        else:
            raise Exception("No such lens unit: " + lens_unit)

        # Set resolution
        bpy.context.scene.render.resolution_x = image_width
        bpy.context.scene.render.resolution_y = image_height

        # Set clipping
        cam.clip_start = clip_start
        cam.clip_end = clip_end

        # Set aspect ratio
        bpy.context.scene.render.pixel_aspect_x = pixel_aspect_x
        bpy.context.scene.render.pixel_aspect_y = pixel_aspect_y

        # Set shift
        cam.shift_x = shift_x
        cam.shift_y = shift_y


    @staticmethod
    def set_stereo_parameters(convergence_mode, convergence_distance, interocular_distance):
        """ Sets the stereo parameters of the camera.

        :param convergence_mode: How the two cameras converge (e.g. Off-Axis where both cameras are shifted inwards to converge in the convergence plane, or parallel where they do not converge and are parallel)
        :param convergence_distance: The convergence point for the stereo cameras (i.e. distance from the projector to the projection screen)
        :param interocular_distance: Distance between the camera pair
        """
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        cam.stereo.convergence_mode = convergence_mode
        cam.stereo.convergence_distance = convergence_distance
        cam.stereo.interocular_distance = interocular_distance

    @staticmethod
    def set_intrinsics_from_K_matrix(K, image_width, image_height, clip_start=0.1, clip_end=1000):
        """ Set the camera intrinsics via a K matrix.

        The K matrix should have the format:
            [[fx, 0, cx],
             [0, fy, cy],
             [0, 0,  1]]

        This method is based on https://blender.stackexchange.com/a/120063.

        :param K: The 3x3 K matrix.
        :param image_width: The image width in pixels.
        :param image_height: The image height in pixels.
        :param clip_start: Clipping start.
        :param clip_end: Clipping end.
        """
        if not isinstance(K, Matrix):
            K = Matrix(K)

        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        fx, fy = K[0][0], K[1][1]
        cx, cy = K[0][2], K[1][2]

        # If fx!=fy change pixel aspect ratio
        pixel_aspect_x = pixel_aspect_y = 1
        if fx > fy:
            pixel_aspect_y = fx / fy
        elif fx < fy:
            pixel_aspect_x = fy / fx

        # Compute sensor size in mm and view in px
        pixel_aspect_ratio = pixel_aspect_y / pixel_aspect_x
        view_fac_in_px = CameraUtility.get_view_fac_in_px(cam, pixel_aspect_x, pixel_aspect_y, image_width, image_height)
        sensor_size_in_mm = CameraUtility.get_sensor_size(cam)

        # Convert focal length in px to focal length in mm
        f_in_mm = fx * sensor_size_in_mm / view_fac_in_px

        # Convert principal point in px to blenders internal format
        shift_x = (cx - (image_width - 1) / 2) / -view_fac_in_px
        shift_y = (cy - (image_height - 1) / 2) / view_fac_in_px * pixel_aspect_ratio

        # Finally set all intrinsics
        CameraUtility.set_intrinsics_from_blender_params(f_in_mm, image_width, image_height, clip_start, clip_end, pixel_aspect_x, pixel_aspect_y, shift_x, shift_y)

    @staticmethod
    def get_sensor_size(cam):
        """ Returns the sensor size in millimeters based on the configured sensor_fit.

        :param cam: The camera object.
        :return: The sensor size in millimeters.
        """
        if cam.sensor_fit == 'VERTICAL':
            sensor_size_in_mm = cam.sensor_height
        else:
            sensor_size_in_mm = cam.sensor_width
        return sensor_size_in_mm

    @staticmethod
    def get_view_fac_in_px(cam, pixel_aspect_x, pixel_aspect_y, resolution_x_in_px, resolution_y_in_px):
        """ Returns the camera view in pixels.

        :param cam: The camera object.
        :param pixel_aspect_x: The pixel aspect ratio along x.
        :param pixel_aspect_y: The pixel aspect ratio along y.
        :param resolution_x_in_px: The image width in pixels.
        :param resolution_y_in_px: The image height in pixels.
        :return: The camera view in pixels.
        """
        # Determine the sensor fit mode to use
        if cam.sensor_fit == 'AUTO':
            if pixel_aspect_x * resolution_x_in_px >= pixel_aspect_y * resolution_y_in_px:
                sensor_fit = 'HORIZONTAL'
            else:
                sensor_fit = 'VERTICAL'
        else:
            sensor_fit = cam.sensor_fit

        # Based on the sensor fit mode, determine the view in pixels
        pixel_aspect_ratio = pixel_aspect_y / pixel_aspect_x
        if sensor_fit == 'HORIZONTAL':
            view_fac_in_px = resolution_x_in_px
        else:
            view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px

        return view_fac_in_px

    @staticmethod
    def get_intrinsics_as_K_matrix():
        """ Returns the current set intrinsics in the form of a K matrix.

        This is basically the inverse of the the set_intrinsics_from_K_matrix() function.

        :return: The 3x3 K matrix
        """
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        f_in_mm = cam.lens
        resolution_x_in_px = bpy.context.scene.render.resolution_x
        resolution_y_in_px = bpy.context.scene.render.resolution_y

        # Compute sensor size in mm and view in px
        pixel_aspect_ratio = bpy.context.scene.render.pixel_aspect_y / bpy.context.scene.render.pixel_aspect_x
        view_fac_in_px = CameraUtility.get_view_fac_in_px(cam, bpy.context.scene.render.pixel_aspect_x, bpy.context.scene.render.pixel_aspect_y, resolution_x_in_px, resolution_y_in_px)
        sensor_size_in_mm = CameraUtility.get_sensor_size(cam)

        # Convert focal length in mm to focal length in px
        fx = f_in_mm / sensor_size_in_mm * view_fac_in_px
        fy = fx / pixel_aspect_ratio

        # Convert principal point in blenders format to px
        cx = (resolution_x_in_px - 1) / 2 - cam.shift_x * view_fac_in_px
        cy = (resolution_y_in_px - 1) / 2 + cam.shift_y * view_fac_in_px / pixel_aspect_ratio

        # Build K matrix
        return Matrix(
            [[fx, 0, cx],
             [0, fy, cy],
             [0, 0, 1]])
