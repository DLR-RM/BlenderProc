from math import fabs, acos
from typing import Union, List
import numpy as np
from sklearn.cluster import MeanShift

import bmesh
import bpy
import mathutils

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.utility.Utility import resolve_path


def extract_floor(mesh_objects: List[MeshObject], compare_angle_degrees: float = 7.5, compare_height: float = 0.15,
                  up_vector_upwards: bool = True, height_list_path: str = None,
                  new_name_for_object: str = "Floor", should_skip_if_object_is_already_there: bool = False) \
        -> List[MeshObject]:
    """ Extracts floors in the following steps:
    1. Searchs for the specified object.
    2. Splits the surfaces which point upwards at a specified level away.

    :param mesh_objects: Objects to where all polygons will be extracted.
    :param compare_angle_degrees: Maximum difference between the up vector and the current polygon normal in degrees.
    :param compare_height: Maximum difference in Z direction between the polygons median point and the specified height of the room.
    :param up_vector_upwards: If this is True the `up_vec` points upwards -> [0, 0, 1] if not it points downwards: [0, 0, -1] in world coordinates. This vector is used for the `compare_angle_degrees` option.
    :param height_list_path: Path to a file with height values. If none is provided, a ceiling and floor is automatically detected. \
                             This might fail. The height_list_values can be specified in a list like fashion in the file: [0.0, 2.0]. \
                             These values are in the same size the dataset is in, which is usually meters. The content must always be \
                             a list, e.g. [0.0].
    :param new_name_for_object: Name for the newly created object, which faces fulfill the given parameters.
    :param should_skip_if_object_is_already_there: If this is true no extraction will be done, if an object is there, which has the same name as
                                                   name_for_split_obj, which would be used for the newly created object.
    :return: The extracted floor objects.
    """
    # set the up_vector
    up_vec = mathutils.Vector([0, 0, 1])
    if not up_vector_upwards:
        up_vec *= -1.0

    height_list = []
    if height_list_path is not None:
        height_file_path = resolve_path(height_list_path)
        with open(height_file_path) as file:
            import ast
            height_list = [float(val) for val in ast.literal_eval(file.read())]

    object_names = [obj.name for obj in bpy.context.scene.objects if obj.type == "MESH"]

    def clean_up_name(name: str):
        """
        Clean up the given name from Floor1 to floor

        :param name: given name
        :return: str: cleaned up name
        """
        name = ''.join([i for i in name if not i.isdigit()])  # remove digits
        name = name.lower().replace(".", "").strip()  # remove dots and whitespace
        return name

    object_names = [clean_up_name(name) for name in object_names]
    if should_skip_if_object_is_already_there and new_name_for_object.lower() in object_names:
        # if should_skip is True and if there is an object, which name is the same as the one for the newly
        # split object, than the execution is skipped
        return []

    newly_created_objects = []
    for obj in mesh_objects:
        obj.edit_mode()
        bm = obj.mesh_as_bmesh()
        bpy.ops.mesh.select_all(action='DESELECT')

        if height_list:
            counter = 0
            for height_val in height_list:
                counter = FloorExtractor.select_at_height_value(bm, height_val, compare_height, up_vec,
                                                                compare_angle_degrees, obj.get_local2world_mat())

            if counter:
                obj.update_from_bmesh(bm)
                bpy.ops.mesh.separate(type='SELECTED')
        else:
            # no height list was provided, try to estimate them on its own

            # first get a list of all height values of the median points, which are inside of the defined
            # compare angle range
            list_of_median_poses: Union[List[float], np.ndarray] = [FloorExtractor._get_median_face_pose(f, obj.get_local2world_mat())[2] for f in
                                    bm.faces if
                                    FloorExtractor._check_face_angle(f, obj.get_local2world_mat(), up_vec,
                                                                     compare_angle_degrees)]
            if not list_of_median_poses:
                print("Object with name: {} is skipped no faces were relevant, try with "
                      "flipped up_vec".format(obj.get_name()))
                list_of_median_poses = [FloorExtractor._get_median_face_pose(f, obj.get_local2world_mat())[2] for f in
                                        bm.faces if FloorExtractor._check_face_angle(f, obj.get_local2world_mat(),
                                                                                     -up_vec, compare_angle_degrees)]
                if not list_of_median_poses:
                    print("Still no success for: {} skip object.".format(obj.get_name()))
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    continue

                successful_up_vec = -up_vec
            else:
                successful_up_vec = up_vec

            list_of_median_poses = np.reshape(list_of_median_poses, (-1, 1))
            if np.var(list_of_median_poses) < 1e-4:
                # All faces are already correct
                height_value = np.mean(list_of_median_poses)
            else:
                ms = MeanShift(bandwidth=0.2, bin_seeding=True)
                ms.fit(list_of_median_poses)

                # if the up vector is negative the maximum value is searched
                if up_vector_upwards:
                    height_value = np.min(ms.cluster_centers_)
                else:
                    height_value = np.max(ms.cluster_centers_)

            counter = FloorExtractor.select_at_height_value(bm, height_value, compare_height, successful_up_vec,
                                                            compare_angle_degrees, obj.get_local2world_mat())

            if counter:
                obj.update_from_bmesh(bm)
                bpy.ops.mesh.separate(type='SELECTED')
            selected_objects = bpy.context.selected_objects
            if selected_objects:
                if len(selected_objects) == 2:
                    selected_objects = [o for o in selected_objects
                                        if o != bpy.context.view_layer.objects.active]
                    selected_objects[0].name = new_name_for_object
                    newly_created_objects.append(MeshObject(selected_objects[0]))
                else:
                    raise Exception("There is more than one selection after splitting, this should not happen!")
            else:
                raise Exception("No floor object was constructed!")

        obj.object_mode()

    return newly_created_objects


class FloorExtractor:

    @staticmethod
    def select_at_height_value(bm: bmesh.types.BMesh, height_value: float, compare_height: float,
                               up_vector: Union[mathutils.Vector, np.ndarray], cmp_angle: float,
                               matrix_world: Union[mathutils.Matrix, np.ndarray]) -> int:
        """
        Selects for a given `height_value` all faces, which are inside the given `compare_height` band and also face
        upwards. This is done by comparing the face.normal in world coordinates to the `up_vector` and the resulting
        angle must be smaller than `compare_angle`.

        :param bm: The object as BMesh in edit mode. The face should be structured, meaning a lookup was performed on \
                   them before.
        :param height_value: Height value which is used for comparing the faces median point against
        :param compare_height: Defines the range in which the face median is compared to the height value.
        :param up_vector: Vector, which is used for comparing the face.normal against
        :param cmp_angle: Angle, which is used to compare against the up_vec in radians.
        :param matrix_world: The matrix_world of the object, to which the face belongs
        """
        # deselect all faces
        counter = 0
        for f in bm.faces:
            if FloorExtractor._check_face_with(f, matrix_world, height_value, compare_height, up_vector, cmp_angle):
                counter += 1
                f.select = True
        print("Selected {} polygons as floor".format(counter))
        return counter

    @staticmethod
    def _get_median_face_pose(face: bmesh.types.BMFace,
                              matrix_world: Union[mathutils.Matrix, np.ndarray]) -> mathutils.Vector:
        """
        Returns the median face pose of all its vertices in the world coordinate frame.

        :param face: Current selected frame, its vertices are used to calculate the median
        :param matrix_world: The matrix of the current object to which this face belongs
        :return: mathutils.Vector(): The current median point of the vertices in world coordinates
        """
        # calculate the median position of the current face
        median_pose = face.calc_center_median().to_4d()
        median_pose[3] = 1.0
        median_pose = mathutils.Matrix(matrix_world) @ median_pose
        return median_pose

    @staticmethod
    def _check_face_angle(face: bmesh.types.BMFace, matrix_world: Union[mathutils.Matrix, np.ndarray],
                          up_vector: Union[mathutils.Vector, np.ndarray], cmp_angle: float) -> bool:
        """
        Checks if a face.normal in world coordinates angular difference to the `up_vec` is closer as
        `cmp_anlge`.

        :param face: The face, which will be checked
        :param matrix_world: The matrix_world of the object, to which the face belongs
        :param up_vector: Vector, which is used for comparing the face.normal against
        :param cmp_angle: Angle, which is used to compare against the up_vec in radians.
        :return: bool: Returns true if the face is close the height_value and is inside of the cmp_angle range
        """
        # calculate the normal
        normal_face = face.normal.to_4d()
        normal_face[3] = 0.0
        normal_face = (mathutils.Matrix(matrix_world) @ normal_face).to_3d()
        # compare the normal to the current up_vec
        return acos(normal_face @ mathutils.Vector(up_vector)) < cmp_angle

    @staticmethod
    def _check_face_with(face: bmesh.types.BMFace, matrix_world: Union[mathutils.Matrix, np.ndarray],
                         height_value: float,
                         cmp_height: float, up_vector: Union[mathutils.Vector, np.ndarray], cmp_angle: float) -> bool:
        """
        Check if the face is on a certain `height_value` by checking if it is inside of the band spanned by
        `cmp_height` -> [`height_value` - `cmp_height`, `height_value` + `cmp_height`] and then if the face
        has a similar angle to the given `up_vec`, the difference must be smaller than `cmp_angle`.

        :param face: The face, which will be checked
        :param matrix_world: The matrix_world of the object, to which the face belongs
        :param height_value: Height value which is used for comparing the faces median point against
        :param cmp_height: Defines the range in which the face median is compared to the height value.
        :param up_vector: Vector, which is used for comparing the face.normal against
        :param cmp_angle: Angle, which is used to compare against the up_vec in radians.
        :return: bool: Returns true if the face is close the height_value and is inside of the cmp_angle range
        """
        median_pose = FloorExtractor._get_median_face_pose(face, matrix_world)

        # compare that pose to the current height_band
        if fabs(median_pose[2] - height_value) < cmp_height:
            return FloorExtractor._check_face_angle(face, matrix_world, up_vector, cmp_angle)
        return False
