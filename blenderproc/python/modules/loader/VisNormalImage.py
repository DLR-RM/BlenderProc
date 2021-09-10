import math

import bpy
import h5py
import mathutils
import numpy as np

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.utility.BlenderUtility import add_object_only_with_direction_vectors
from blenderproc.python.utility.Utility import resolve_path


class VisNormalImage(Module):
    """ This module can visualize a .hdf5 container containing a normal and a distance image and also the campose,
        this can be used while debugging to make sure that the resulting distance and normal image are as intended.

        Necessary keys in the .hdf5 container are:
            * distance: (X, Y) or (X, Y, 3)
            * normal: (X, Y, 3)
            * campose: string written by the CameraStateWriter

    *8Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - path_to_hdf5
          - The file path to the hdf5 container.
          - string
        * - max_distance
          - Maximum distance to be considered. Default: 24.
          - float
        * - normal_length
          - Length of the normal edge in the scene. Default: 0.1.
          - float
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):

        max_distance = self.config.get_float("max_distance", 24)
        normal_len = self.config.get_float("normal_length", 0.1)

        path_to_hdf5 = resolve_path(self.config.get_string("path_to_hdf5"))
        data = {}
        with h5py.File(path_to_hdf5, "r") as file:
            for key in file.keys():
                data[key] = np.array(file[key])

        if "normals" not in data:
            raise Exception("The hdf5 container does not contain normals: {}".format(path_to_hdf5))
        if "distance" not in data:
            raise Exception("The hdf5 container does not contain distance data: {}".format(path_to_hdf5))
        if "campose" not in data:
            raise Exception("The hdf5 container does not contain a camera pose: {}".format(path_to_hdf5))

        normal_img = data["normals"]
        distance_img = data["distance"]
        campose = eval(data["campose"])[0]
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data
        cam_ob.location = campose["location"]
        cam_ob.rotation_euler = campose["rotation_euler"]
        cam.angle_x = campose["fov_x"]
        cam.angle_y = campose["fov_y"]
        bpy.context.scene.render.resolution_x = distance_img.shape[1]
        bpy.context.scene.render.resolution_y = distance_img.shape[0]
        bpy.context.view_layer.update()

        cam_matrix = cam_ob.matrix_world
        # This might not be completely correct, but the fov_y value is off
        x_angle = cam.angle_x * 0.5

        tan_angle_x = math.tan(x_angle)
        tan_angle_y = math.tan(x_angle) * (float(distance_img.shape[0]) / distance_img.shape[1])
        vertices = []
        normals = []
        rot_mat_camera = mathutils.Matrix([[ele for ele in rows[:3]] for rows in cam_ob.matrix_world[:3]])
        for i in range(distance_img.shape[0]):
            for j in range(distance_img.shape[1]):
                if len(distance_img.shape) == 2:
                    distance_value = distance_img[i,j]
                else:
                    distance_value = distance_img[i,j,0]
                if distance_value < max_distance:
                    # Convert principal point cx,cy in px to blender cam shift in proportion to larger image dim
                    x_center = float(j - distance_img.shape[1] * 0.5) / distance_img.shape[1] * 2
                    y_center = float(i - distance_img.shape[0] * 0.5) / distance_img.shape[0] * 2 * -1
                    coord_x = x_center * tan_angle_x
                    coord_y = y_center * tan_angle_y
                    beam = mathutils.Vector([coord_x, coord_y, -1])
                    beam.normalize()
                    beam *= distance_value

                    location = cam_matrix @ beam
                    vertices.append(mathutils.Vector(location))
                    normal = mathutils.Vector([(ele - 0.5) * 2.0 for ele in normal_img[i, j]])
                    normal = rot_mat_camera @ normal
                    normals.append(normal)

        add_object_only_with_direction_vectors(vertices, normals, radius=normal_len, name='NewVertexObject')
