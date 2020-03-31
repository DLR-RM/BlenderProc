import math

import mathutils
import bpy

from src.main.Module import Module
from src.utility.BlenderUtility import load_image
from src.utility.BlenderUtility import add_object_only_with_direction_vectors
from src.utility.Utility import Utility

class VisNormalImage(Module):

    def __init__(self, config):
        Module.__init__(self, config)


    def run(self):

        path_to_normal_image = Utility.resolve_path(self.config.get_string("path_to_normal_image"))
        path_to_depth_image = Utility.resolve_path(self.config.get_string("path_to_depth_image"))

        self.normal_img = load_image(path_to_normal_image)
        self.depth_img = load_image(path_to_depth_image)

        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data
        cam_matrix = cam_ob.matrix_world

        x_angle = cam.angle_x * 0.5
        y_angle = cam.angle_x * 0.5
        spacing = 1
        vertices = []
        normals = []
        rot_mat_camera = mathutils.Matrix([[ele for ele in rows[:3]] for rows in cam_ob.matrix_world[:3]])
        for i in range(0, self.depth_img.shape[0], spacing):
            for j in range(0, self.depth_img.shape[1], spacing):
                depth_value = self.depth_img[i,j,0]
                if depth_value < 24:
                    # Convert principal point cx,cy in px to blender cam shift in proportion to larger image dim
                    y_center = -1 * float(i - self.depth_img.shape[0] * 0.5) / self.depth_img.shape[0] * 2
                    x_center = float(j - self.depth_img.shape[1] * 0.5) / self.depth_img.shape[1] * 2
                    coord_x = x_center * math.tan(x_angle)
                    coord_y = y_center * math.tan(y_angle)
                    beam = mathutils.Vector([coord_x, coord_y, -1])
                    beam.normalize()
                    beam *= depth_value

                    location = cam_matrix @ beam
                    vertices.append(mathutils.Vector(location))
                    normal = mathutils.Vector([(ele - 0.5) * 2.0 for ele in self.normal_img[i, j]])
                    normal = rot_mat_camera @ normal
                    normals.append(normal)

        add_object_only_with_direction_vectors(vertices, normals, radius=0.1, name='NewVertexObject')







