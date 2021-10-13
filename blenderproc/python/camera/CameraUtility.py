import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler
from typing import Union, Tuple, Optional

from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.utility.Utility import KeyFrame


def add_camera_pose(cam2world_matrix: Union[np.ndarray, Matrix], frame: Optional[int] = None) -> int:
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


def get_camera_pose(frame: Optional[int] = None) -> np.ndarray:
    """ Returns the camera pose in the form of a 4x4 cam2world transformation matrx.

    :param frame: The frame number whose assigned camera pose should be returned. If None is give, the current frame is used.
    :return: The 4x4 cam2world transformation matrix.
    """
    with KeyFrame(frame):
        return np.array(Entity(bpy.context.scene.camera).get_local2world_mat())


def rotation_from_forward_vec(forward_vec: Union[np.ndarray, Vector], up_axis: str = 'Y',
                              inplane_rot: Optional[float] = None) -> np.ndarray:
    """ Returns a camera rotation matrix for the given forward vector and up axis

    :param forward_vec: The forward vector which specifies the direction the camera should look.
    :param up_axis: The up axis, usually Y.
    :param inplane_rot: The inplane rotation in radians. If None is given, the inplane rotation is determined only based on the up vector.
    :return: The corresponding rotation matrix.
    """
    rotation_matrix = Vector(forward_vec).to_track_quat('-Z', up_axis).to_matrix()
    if inplane_rot is not None:
        rotation_matrix = rotation_matrix @ Euler((0.0, 0.0, inplane_rot)).to_matrix()
    return np.array(rotation_matrix)

def set_resolution(image_width: int = None, image_height: int = None):
    """ Sets the camera resolution.
    
    :param image_width: The image width in pixels.
    :param image_height: The image height in pixels.
    """
    set_intrinsics_from_blender_params(None, image_width, image_height)


def set_intrinsics_from_blender_params(lens: float = None, image_width: int = None, image_height: int = None, clip_start: float = None, clip_end: float = None, 
                                       pixel_aspect_x: float = None, pixel_aspect_y: float = None, shift_x: int = None, shift_y: int = None, lens_unit: str = None):
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

    if lens_unit is not None:
        cam.lens_unit = lens_unit
        
    if lens is not None:
        # Set focal length
        if cam.lens_unit == 'MILLIMETERS':
            if lens < 1:
                raise Exception("The focal length is smaller than 1mm which is not allowed in blender: " + str(lens))
            cam.lens = lens
        elif cam.lens_unit == "FOV":
            cam.angle = lens
        else:
            raise Exception("No such lens unit: " + lens_unit)

    # Set resolution
    if image_width is not None:
        bpy.context.scene.render.resolution_x = image_width
    if image_height is not None:
        bpy.context.scene.render.resolution_y = image_height
        
    # Set clipping
    if clip_start is not None:
        cam.clip_start = clip_start
    if clip_end is not None:
        cam.clip_end = clip_end

    # Set aspect ratio
    if pixel_aspect_x is not None:
        bpy.context.scene.render.pixel_aspect_x = pixel_aspect_x
    if pixel_aspect_y is not None:
        bpy.context.scene.render.pixel_aspect_y = pixel_aspect_y

    # Set shift
    if shift_x is not None:
        cam.shift_x = shift_x
    if shift_y is not None:
        cam.shift_y = shift_y

def set_stereo_parameters(convergence_mode: str, convergence_distance: float, interocular_distance: float):
    """ Sets the stereo parameters of the camera.

    :param convergence_mode: How the two cameras converge (e.g. Off-Axis where both cameras are shifted inwards to converge in the convergence plane, or parallel where they do not converge and are parallel). Available: ["OFFAXIS", "PARALLEL", "TOE"]
    :param convergence_distance: The convergence point for the stereo cameras (i.e. distance from the projector to the projection screen)
    :param interocular_distance: Distance between the camera pair
    """
    cam_ob = bpy.context.scene.camera
    cam = cam_ob.data

    cam.stereo.convergence_mode = convergence_mode
    cam.stereo.convergence_distance = convergence_distance
    cam.stereo.interocular_distance = interocular_distance


def set_intrinsics_from_K_matrix(K: Union[np.ndarray, Matrix], image_width: int, image_height: int,
                                 clip_start: float = None, clip_end: float = None):
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
    view_fac_in_px = get_view_fac_in_px(cam, pixel_aspect_x, pixel_aspect_y, image_width, image_height)
    sensor_size_in_mm = get_sensor_size(cam)

    # Convert focal length in px to focal length in mm
    f_in_mm = fx * sensor_size_in_mm / view_fac_in_px

    # Convert principal point in px to blenders internal format
    shift_x = (cx - (image_width - 1) / 2) / -view_fac_in_px
    shift_y = (cy - (image_height - 1) / 2) / view_fac_in_px * pixel_aspect_ratio

    # Finally set all intrinsics
    set_intrinsics_from_blender_params(f_in_mm, image_width, image_height, clip_start, clip_end, pixel_aspect_x, pixel_aspect_y, shift_x, shift_y, "MILLIMETERS")


def get_sensor_size(cam: bpy.types.Camera) -> float:
    """ Returns the sensor size in millimeters based on the configured sensor_fit.

    :param cam: The camera object.
    :return: The sensor size in millimeters.
    """
    if cam.sensor_fit == 'VERTICAL':
        sensor_size_in_mm = cam.sensor_height
    else:
        sensor_size_in_mm = cam.sensor_width
    return sensor_size_in_mm


def get_view_fac_in_px(cam: bpy.types.Camera, pixel_aspect_x: float, pixel_aspect_y: float,
                       resolution_x_in_px: int, resolution_y_in_px: int) -> int:
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


def get_intrinsics_as_K_matrix() -> np.ndarray:
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
    view_fac_in_px = get_view_fac_in_px(cam, bpy.context.scene.render.pixel_aspect_x, bpy.context.scene.render.pixel_aspect_y, resolution_x_in_px, resolution_y_in_px)
    sensor_size_in_mm = get_sensor_size(cam)

    # Convert focal length in mm to focal length in px
    fx = f_in_mm / sensor_size_in_mm * view_fac_in_px
    fy = fx / pixel_aspect_ratio

    # Convert principal point in blenders format to px
    cx = (resolution_x_in_px - 1) / 2 - cam.shift_x * view_fac_in_px
    cy = (resolution_y_in_px - 1) / 2 + cam.shift_y * view_fac_in_px / pixel_aspect_ratio

    # Build K matrix
    K = np.array([[fx, 0, cx],
                  [0, fy, cy],
                  [0, 0, 1]])
    return K


def get_fov() -> Tuple[float, float]:
    """ Returns the horizontal and vertical FOV of the current camera.

    Blender also offers the current FOV as direct attributes of the camera object, however
    at least the vertical FOV heavily differs from how it would usually be defined.

    :return: The horizontal and vertical FOV in radians.
    """
    # Get focal length
    K = get_intrinsics_as_K_matrix()
    # Convert focal length to FOV
    fov_x = 2 * np.arctan(bpy.context.scene.render.resolution_x / 2 / K[0, 0])
    fov_y = 2 * np.arctan(bpy.context.scene.render.resolution_y / 2 / K[1, 1])
    return fov_x, fov_y


def add_depth_of_field(focal_point_obj: Entity, fstop_value: float,
                       aperture_blades: int = 0, aperture_rotation: float = 0.0, aperture_ratio: float = 1.0,
                       focal_distance: float = -1.0):
    """
    Adds depth of field to the given camera, the focal point will be set by the focal_point_obj, ideally an empty
    instance is used for this see `bproc.object.create_empty()` on how to init one of those. A higher fstop value
    makes the resulting image look sharper, while a low value decreases the sharpness.

    Check the documentation on
    https://docs.blender.org/manual/en/latest/render/cameras.html#depth-of-field

    :param focal_point_obj: The used focal point, if the object moves the focal point will move with it
    :param fstop_value: A higher fstop value, will increase the sharpness of the scene
    :param aperture_blades: Amount of blades used in the camera
    :param aperture_rotation: Rotation of the blades in the camera in radiant
    :param aperture_ratio: Ratio of the anamorphic bokeh effect, below 1.0 will give a horizontal one, above one a \
                           vertical one.
    :param focal_distance: Sets the distance to the focal point when no focal_point_obj is given.
    """
    cam_ob = bpy.context.scene.camera
    camera = cam_ob.data

    # activate depth of field rendering for this camera
    camera.dof.use_dof = True
    if focal_point_obj is not None:
        # set the focus point of the camera
        camera.dof.focus_object = focal_point_obj.blender_obj
    elif focal_distance >= 0.0:
        camera.dof.focus_distance = focal_distance
    else:
        raise RuntimeError("Either a focal_point_obj have to be given or the focal_distance has to be higher "
                           "than zero.")
    # set the aperture of the camera, lower values make the scene more out of focus, higher values make them look
    # sharper
    camera.dof.aperture_fstop = fstop_value
    # set the amount of blades
    camera.dof.aperture_blades = aperture_blades
    # setting the rotation of the aperture in radiant
    camera.dof.aperture_rotation = aperture_rotation
    # Change the amount of distortion to simulate the anamorphic bokeh effect. A setting of 1.0 shows no
    # distortion, where a number below 1.0 will cause a horizontal distortion, and a higher number will
    # cause a vertical distortion.
    camera.dof.aperture_ratio = aperture_ratio
