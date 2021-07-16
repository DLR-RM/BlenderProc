import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler
from typing import Union, List

class MathUtility:

    @staticmethod
    def transform_point_to_blender_coord_frame(point: Union[np.ndarray, list, Vector], frame_of_point: List[str]) -> np.ndarray:
        """ Transforms the given point into the blender coordinate frame.

        Example: [1, 2, 3] and ["X", "-Z", "Y"] => [1, -3, 2]

        :param point: The point to convert in form of a np.ndarray, list or mathutils.Vector.
        :param frame_of_point: An array containing three elements, describing the axes of the coordinate frame the point is in. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
        :return: The converted point also in form of a list or mathutils.Vector.
        """
        assert len(frame_of_point) == 3, "The specified coordinate frame has more or less than tree axes: {}".format(frame_of_point)
        point = np.array(point)

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

        return np.array(output)

    @staticmethod
    def transform_matrix_to_blender_coord_frame(matrix: Union[np.ndarray, Matrix], source_frame: List[str]) -> np.ndarray:
        """ Transforms the given homog into the blender coordinate frame.

        :param matrix: The matrix to convert in form of a np.ndarray or mathutils.Matrix
        :param frame_of_point: An array containing three elements, describing the axes of the coordinate frame of the \
                            source frame. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
        :return: The converted matrix is in form of a np.ndarray
        """
        assert len(source_frame) == 3, "The specified coordinate frame has more or less than tree axes: {}".format(frame_of_point)
        matrix = Matrix(matrix)

        output = np.eye(4)
        for i, axis in enumerate(source_frame):
            axis = axis.upper()

            if axis.endswith("X"):
                output[:4,0] = matrix.col[0]
            elif axis.endswith("Y"):
                output[:4,1] = matrix.col[1]
            elif axis.endswith("Z"):
                output[:4,2] = matrix.col[2]
            else:
                raise Exception("Invalid axis: " + axis)

            if axis.startswith("-"):
                output[:3, i] *= -1

        output[:4,3] = matrix.col[3]
        return output

    @staticmethod
    def transform_matrix_to_blender_coord_frame(matrix: Matrix, source_frame: list) -> Matrix:
        """ Transforms the given homog into the blender coordinate frame.

        :param matrix: The matrix to convert in form of a mathutils.Matrix.
        :param source_frame: An array containing three elements, describing the axes of the coordinate frame of the \
                               source frame. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
        :return: The converted point is in form of a mathutils.Matrix.
        """
        assert len(source_frame) == 3, "The specified coordinate frame has more or less than tree axes: {}".format(source_frame)
        matrix = np.array(matrix)

        # Build transformation matrix that maps the given matrix to the specified coordinate frame.
        tmat = np.zeros((4, 4))
        for i, axis in enumerate(source_frame):
            axis = axis.upper()

            if axis.endswith("X"):
                tmat[i, 0] = 1
            elif axis.endswith("Y"):
                tmat[i, 1] = 1
            elif axis.endswith("Z"):
                tmat[i, 2] = 1
            else:
                raise Exception("Invalid axis: " + axis)

            if axis.startswith("-"):
                tmat[i] *= -1
        tmat[3, 3] = 1

        # Apply transformation matrix
        output = np.matmul(tmat, matrix)
        output = Matrix(output)
        return output

    @staticmethod
    def build_transformation_mat(translation: Union[np.ndarray, list, Vector], rotation: Union[np.ndarray, List[list], Matrix]) -> np.ndarray:
        """ Build a transformation matrix from translation and rotation parts.

        :param translation: A (3,) vector representing the translation part.
        :param rotation: A 3x3 rotation matrix or Euler angles of shape (3,).
        :return: The 4x4 transformation matrix.
        """
        translation = np.array(translation)
        rotation = np.array(rotation)

        mat = np.eye(4)
        if translation.shape[0] == 3:
            mat[:3, 3] = translation
        else:
            raise Exception("translation has invalid shape: {}. Must be (3,) or (3,1) vector.".format(translation.shape))
        if rotation.shape == (3,3):
            mat[:3,:3] = rotation
        elif rotation.shape[0] == 3:
            mat[:3,:3] = np.array(Euler(rotation).to_matrix())
        else:
            raise Exception("rotation has invalid shape: {}. Must be rotation matrix of shape (3,3) or Euler angles of shape (3,) or (3,1).".format(rotation.shape))

        return mat
