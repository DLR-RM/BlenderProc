import math

import mathutils
import bpy
import numpy as np
import h5py

from src.main.Module import Module
from src.utility.BlenderUtility import add_object_only_with_direction_vectors
from src.utility.Utility import Utility


class VisNormalImage(Module):
    """ This module can visualize a .hdf5 container containing a normal and a depth image and also the campose,
        this can be used while debugging to make sure that the resulting depth and normal image are as intended.

        Necessary keys in the .hdf5 container are:
            * depth: (X, Y) or (X, Y, 3)
            * normal: (X, Y, 3)
            * campose: string written by the CameraStateWriter

    *8Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "path_to_hdf5", "The file path to the hdf5 container. Type: string."
        "max_depth", "Maximum depth to be considered. Type: float. Default: 24."
        "normal_length", "Length of the normal edge in the scene. Type: float. Default: 0.1."
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):

        max_depth = self.config.get_float("max_depth", 24)
        normal_len = self.config.get_float("normal_length", 0.1)

        path_to_hdf5 = Utility.resolve_path(self.config.get_string("path_to_hdf5"))
        data = {}
        with h5py.File(path_to_hdf5, "r") as file:
            for key in file.keys():
                data[key] = np.array(file[key])

        if "normals" not in data:
            raise Exception("The hdf5 container does not contain normals: {}".format(path_to_hdf5))
        if "depth" not in data:
            raise Exception("The hdf5 container does not contain depth data: {}".format(path_to_hdf5))
        if "campose" not in data:
            raise Exception("The hdf5 container does not contain a camera pose: {}".format(path_to_hdf5))

        normal_img = data["normals"]
        depth_img = data["depth"]
        campose = eval(data["campose"])[0]
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data
        cam_ob.location = campose["location"]
        cam_ob.rotation_euler = campose["rotation_euler"]
        cam.angle_x = campose["fov_x"]
        cam.angle_y = campose["fov_y"]
        bpy.context.scene.render.resolution_x = depth_img.shape[1]
        bpy.context.scene.render.resolution_y = depth_img.shape[0]
        bpy.context.view_layer.update()

        cam_matrix = cam_ob.matrix_world
        # This might not be completely correct, but the fov_y value is off
        x_angle = cam.angle_x * 0.5

        tan_angle_x = math.tan(x_angle)
        tan_angle_y = math.tan(x_angle) * (float(depth_img.shape[0]) / depth_img.shape[1])
        vertices = []
        normals = []
        rot_mat_camera = mathutils.Matrix([[ele for ele in rows[:3]] for rows in cam_ob.matrix_world[:3]])
        for i in range(depth_img.shape[0]):
            for j in range(depth_img.shape[1]):
                if len(depth_img.shape) == 2:
                    depth_value = depth_img[i,j]
                else:
                    depth_value = depth_img[i,j,0]
                if depth_value < max_depth:
                    # Convert principal point cx,cy in px to blender cam shift in proportion to larger image dim
                    x_center = float(j - depth_img.shape[1] * 0.5) / depth_img.shape[1] * 2
                    y_center = float(i - depth_img.shape[0] * 0.5) / depth_img.shape[0] * 2 * -1
                    coord_x = x_center * tan_angle_x
                    coord_y = y_center * tan_angle_y
                    beam = mathutils.Vector([coord_x, coord_y, -1])
                    beam.normalize()
                    beam *= depth_value

                    location = cam_matrix @ beam
                    vertices.append(mathutils.Vector(location))
                    normal = mathutils.Vector([(ele - 0.5) * 2.0 for ele in normal_img[i, j]])
                    normal = rot_mat_camera @ normal
                    normals.append(normal)

        add_object_only_with_direction_vectors(vertices, normals, radius=normal_len, name='NewVertexObject')
