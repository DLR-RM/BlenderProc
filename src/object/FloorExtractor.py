import os
import warnings
from math import radians, fabs, acos

import bmesh
import bpy
import mathutils
import numpy as np

from src.loader.LoaderInterface import LoaderInterface
from src.main.Module import Module
from src.utility.Config import Config
from src.utility.Utility import Utility


class FloorExtractor(Module):
    """
    Will search for the specified object and splits the surfaces which point upwards at a specified level away

    Example 1, in which no height_list_path is set, here the floor is extracted automatically. By finding the group
    of polygons with the lowest median in Z direction.

    .. code-block:: yaml

        {
          "module": "object.FloorExtractor",
          "config": {
            "selector": {  # this will select the object, which gets splitt up
              "provider": "getter.Entity",
              "conditions": {
                "name": "wall"
              }
            },
            "compare_angle_degrees" : 7.5,  # this is the maximum angle in degree, in which the face can be twisted
            "compare_height": 0.15,  # the compare height is used after finding the floor
          }
        }

    Example 2, here the ceiling is extracted and not the floor. This is done by using the `up_vector_upwards` key,
    which is set to False here, so the polygons have to face in `[0, 0, -1]` direction. This will also flip, the search
    mechanism, now the highest group of polygons are used, not the lowest.

    .. code-block:: yaml

        {
          "module": "object.FloorExtractor",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": "wall"  # the wall object here contains the ceiling
              }
            },
            "up_vector_upwards": False,  # the polygons are now facing downwards: [0, 0, -1]
            "compare_angle_degrees" : 7.5,
            "compare_height": 0.15,
            "name_for_split_obj": "Ceiling"  # this is the new name of the object
          }
        }

    Example 3, if you are using this to extract the floor of replica scenes, to place objects on top of them.

    .. code-block:: yaml

        {
          "module": "object.FloorExtractor",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": "mesh"  # the wall object here contains the ceiling
              }
            },
            "compare_angle_degrees" : 7.5,
            "compare_height": 0.15,
            "name_for_split_obj": "floor"
          }
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - selector
          - Objects to where all polygons will be extracted.
          - Provider
        * - compare_angle_degrees
          - Maximum difference between the up vector and the current polygon normal in degrees. Default: 7.5.
          - float
        * - compare_height
          - Maximum difference in Z direction between the polygons median point and the specified height of the
            room. Default: 0.15.
          - float
        * - height_list_path
          - Path to a file with height values. If none is provided, a ceiling and floor is automatically detected. \
            This might fail. The height_list_values can be specified in a list like fashion in the file: [0.0, 2.0]. \
            These values are in the same size the dataset is in, which is usually meters. The content must always be \
            a list, e.g. [0.0].
          - string
        * - name_for_split_obj
          - Name for the newly created object, which faces fulfill the given parameters. Default: "Floor".
          - string
        * - up_vector_upwards
          - If this is True the `up_vec` points upwards -> [0, 0, 1] if not it points downwards: [0, 0, -1] in world \
            coordinates. This vector is used for the `compare_angle_degrees` option. Default: True.
          - bool
        * - add_properties
          - With `add_properties` it is possible to set custom properties for the newly separated objects. Use `cp_` \
            prefix for keys.
          - dict
        * - should_skip_if_object_is_already_there
          - If this is true no extraction will be done, if an object is there, which has the same name as
            name_for_split_obj, which would be used for the newly created object. Default: False.
          - bool
    """

    def __init__(self, config):
        Module.__init__(self, config)

    @staticmethod
    def split_at_height_value(bm: bmesh.types.BMesh, height_value: float, compare_height: float,
                              up_vector: mathutils.Vector, cmp_angle: float, matrix_world: mathutils.Matrix):
        """
        Splits for a given `height_value` all faces, which are inside the given `compare_height` band and also face
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
            if FloorExtractor.check_face_with(f, matrix_world, height_value, compare_height, up_vector, cmp_angle):
                counter += 1
                f.select = True
        print("Selected {} polygons as floor".format(counter))
        return counter


    def run(self):
        """ Extracts floors in the following steps:
        1. Searchs for the specified object.
        2. Splits the surfaces which point upwards at a specified level away.
        """

        entities = self.config.get_list("selector")
        compare_angle = radians(self.config.get_float('compare_angle_degrees', 7.5))
        compare_height = self.config.get_float('compare_height', 0.15)
        new_name_for_object = self.config.get_string("name_for_split_obj", "Floor")
        add_properties = self.config.get_raw_dict("add_properties", {})
        should_skip_if_object_is_already_there = self.config.get_bool("should_skip_if_object_is_already_there", False)

        # set the up_vector
        up_vec = mathutils.Vector([0, 0, 1])
        up_vec_upwards = self.config.get_bool("up_vector_upwards", True)
        if not up_vec_upwards:
            up_vec *= -1.0

        height_list = []
        if self.config.has_param("height_list_path"):
            height_file_path = Utility.resolve_path(self.config.get_string('height_list_path'))
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
            return

        bpy.ops.object.select_all(action='DESELECT')
        newly_created_objects = []
        for obj in entities:
            if obj.type != "MESH":
                warnings.warn("The object: {} is not a mesh but was selected in the FloorExtractor!".format(obj.name))
                continue
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            mesh = obj.data
            bm = bmesh.from_edit_mesh(mesh)
            bm.faces.ensure_lookup_table()

            if height_list:
                bpy.ops.mesh.select_all(action='DESELECT')
                counter = 0
                for height_val in height_list:
                    counter = FloorExtractor.split_at_height_value(bm, height_val, compare_height, up_vec,
                                                                   compare_angle, obj.matrix_world)
                if counter:
                    bpy.ops.mesh.separate(type='SELECTED')
            else:
                try:
                    from sklearn.cluster import MeanShift, estimate_bandwidth
                except ImportError:
                    raise ImportError("If no height_list_path is defined, the sklearn lib has to be installed: "
                                      "By adding \"scikit-learn\" to the \"setup\"/\"pip\" in the config file.")

                # no height list was provided, try to estimate them on its own

                # first get a list of all height values of the median points, which are inside of the defined
                # compare angle range
                list_of_median_poses = [FloorExtractor.get_median_face_pose(f, obj.matrix_world)[2] for f in bm.faces if
                                        FloorExtractor.check_face_angle(f, obj.matrix_world, up_vec, compare_angle)]
                if not list_of_median_poses:
                    print("Object with name: {} is skipped no faces were relevant, try with "
                          "flipped up_vec".format(obj.name))
                    list_of_median_poses = [FloorExtractor.get_median_face_pose(f, obj.matrix_world)[2] for f in
                                            bm.faces if FloorExtractor.check_face_angle(f, obj.matrix_world,
                                                                                        -up_vec, compare_angle)]
                    if not list_of_median_poses:
                        print("Still no success for: {} skip object.".format(obj.name))
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
                    if up_vec_upwards:
                        height_value = np.min(ms.cluster_centers_)
                    else:
                        height_value = np.max(ms.cluster_centers_)
                bpy.ops.mesh.select_all(action='DESELECT')
                counter = FloorExtractor.split_at_height_value(bm, height_value, compare_height, successful_up_vec,
                                                               compare_angle, obj.matrix_world)
                if counter:
                    bpy.ops.mesh.separate(type='SELECTED')
                selected_objects = bpy.context.selected_objects
                if selected_objects:
                    if len(selected_objects) == 2:
                        selected_objects = [o for o in selected_objects
                                            if o != bpy.context.view_layer.objects.active]
                        selected_objects[0].name = new_name_for_object
                        newly_created_objects.append(selected_objects[0])
                    else:
                        raise Exception("There is more than one selection after splitting, this should not happen!")
                else:
                    raise Exception("No floor object was constructed!")

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

        if add_properties:
            config = Config({"add_properties": add_properties})
            loader_interface = LoaderInterface(config)
            loader_interface._set_properties(newly_created_objects)

    @staticmethod
    def get_median_face_pose(face: bmesh.types.BMFace, matrix_world: mathutils.Matrix):
        """
        Returns the median face pose of all its vertices in the world coordinate frame.

        :param face: Current selected frame, its vertices are used to calculate the median
        :param matrix_world: The matrix of the current object to which this face belongs
        :return: mathutils.Vector(): The current median point of the vertices in world coordinates
        """
        # calculate the median position of the current face
        median_pose = face.calc_center_median().to_4d()
        median_pose[3] = 1.0
        median_pose = matrix_world @ median_pose
        return median_pose

    @staticmethod
    def check_face_angle(face: bmesh.types.BMFace, matrix_world: mathutils.Matrix,
                         up_vector: mathutils.Vector, cmp_angle: float):
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
        normal_face = (matrix_world @ normal_face).to_3d()
        # compare the normal to the current up_vec
        return acos(normal_face @ up_vector) < cmp_angle

    @staticmethod
    def check_face_with(face: bmesh.types.BMFace, matrix_world: mathutils.Matrix, height_value: float,
                        cmp_height: float, up_vector: mathutils.Vector, cmp_angle: float):
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
        median_pose = FloorExtractor.get_median_face_pose(face, matrix_world)

        # compare that pose to the current height_band
        if fabs(median_pose[2] - height_value) < cmp_height:
            return FloorExtractor.check_face_angle(face, matrix_world, up_vector, cmp_angle)
        return False
