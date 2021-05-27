import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler

class MathUtility:

    @staticmethod
    def t_mat_from_R_t(rotation_matrix, translation_vector):
        """ Returns the transformation matrix from a given rotatation matrix and translation vector

        :param rotation_matrix: The 3x3 rotation matrix
        :param translation_vector: The 3-dim translation vector
        :return: The 4x4 transformation matrix
        """
        return Matrix.Translation(translation_vector) @ rotation_matrix.to_4x4()

    @staticmethod
    def transform_point_to_blender_coord_frame(point, frame_of_point):
        """ Transforms the given point into the blender coordinate frame.

        Example: [1, 2, 3] and ["X", "-Z", "Y"] => [1, -3, 2]

        :param point: The point to convert in form of a list or mathutils.Vector.
        :param frame_of_point: An array containing three elements, describing the axes of the coordinate frame the point is in. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
        :return: The converted point also in form of a list or mathutils.Vector.
        """
        assert len(frame_of_point) == 3, "The specified coordinate frame has more or less than tree axes: {}".format(frame_of_point)

        output = []
        for i, axis in enumerate(frame_of_point):
            axis = axis.upper()

            if axis.endswith("X"):
                output.append(point[0])
            elif axis.endswith("Y"):
                output.append(point[1])
            elif axis.endswith("Z"):
                output.append(point[2])
            else:
                raise Exception("Invalid axis: " + axis)

            if axis.startswith("-"):
                output[-1] *= -1

        # Depending on the given type, return a vector or a list
        if isinstance(point, Vector):
            return Vector(output)
        else:
            return output

    @staticmethod
    def build_t_mat(translation: Vector, rotation: Matrix) -> Matrix:
        """ Build a transformation matrix from translation and rotation parts.

        :param translation: A vector representing the translation part.
        :param rotation: A 3x3 rotation matrix.
        :return: The 4x4 transformation matrix.
        """
        return Matrix.Translation(translation) @ rotation.to_4x4()