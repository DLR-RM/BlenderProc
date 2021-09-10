import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler
from typing import Union, List

def change_coordinate_frame_of_point(point: Union[np.ndarray, list, Vector], new_frame: List[str]) -> np.ndarray:
    """ Transforms the given point into another coordinate frame.

    Example: [1, 2, 3] and ["X", "-Z", "Y"] => [1, -3, 2]

    :param point: The point to convert in form of a np.ndarray, list or mathutils.Vector.
    :param new_frame: An array containing three elements, describing each axis of the new coordinate frame based on the axes of the current frame. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
    :return: The converted point also in form of a np.ndarray
    """
    assert len(new_frame) == 3, "The specified coordinate frame has more or less than tree axes: {}".format(new_frame)
    point = np.array(point)

    output = []
    for i, axis in enumerate(new_frame):
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

def change_target_coordinate_frame_of_transformation_matrix(matrix: Union[np.ndarray, Matrix], new_frame: list) -> np.ndarray:
    """ Changes the coordinate frame the given transformation matrix is mapping to.

    Given a matrix $T_A^B$ that maps from A to B, this function can be used
    to change the axes of B into B' and therefore end up with $T_A^B'$.

    :param matrix: The matrix to convert in form of a np.ndarray or mathutils.Matrix
    :param new_frame: An array containing three elements, describing each axis of the new coordinate frame based on the axes of the current frame. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
    :return: The converted matrix is in form of a np.ndarray
    """
    tmat = MathUtility._build_coordinate_frame_changing_transformation_matrix(new_frame)

    # Apply transformation matrix
    output = np.matmul(tmat, matrix)
    return output

def change_source_coordinate_frame_of_transformation_matrix(matrix: Union[np.ndarray, Matrix], new_frame: list) -> np.ndarray:
    """ Changes the coordinate frame the given transformation matrix is mapping from.

    Given a matrix $T_A^B$ that maps from A to B, this function can be used
    to change the axes of A into A' and therefore end up with $T_A'^B$.

    :param matrix: The matrix to convert in form of a np.ndarray or mathutils.Matrix
    :param new_frame: An array containing three elements, describing each axis of the new coordinate frame based on the axes of the current frame. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
    :return: The converted matrix is in form of a np.ndarray
    """
    tmat = MathUtility._build_coordinate_frame_changing_transformation_matrix(new_frame)
    tmat = np.linalg.inv(tmat)

    # Apply transformation matrix
    output = np.matmul(matrix, tmat)
    return output

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

class MathUtility:

    @staticmethod
    def _build_coordinate_frame_changing_transformation_matrix(destination_frame: list) -> np.ndarray:
        """ Builds a transformation matrix that switches the coordinate frame.

        :param destination_frame: An array containing three elements, describing each axis of the destination coordinate frame based on the axes of the source frame. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
        :return: The transformation matrix
        """
        assert len(destination_frame) == 3, "The specified coordinate frame has more or less than tree axes: {}".format(destination_frame)

        # Build transformation matrix that maps the given matrix to the specified coordinate frame.
        tmat = np.zeros((4, 4))
        for i, axis in enumerate(destination_frame):
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
        return tmat
