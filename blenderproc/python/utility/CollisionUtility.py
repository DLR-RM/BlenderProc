import mathutils
import numpy as np
from mathutils import Vector, Euler, Matrix
from typing import Union, Optional, Dict, Tuple, List
import bpy

from blenderproc.python.types.MeshObjectUtility import MeshObject


class CollisionUtility:

    @staticmethod
    def check_intersections(obj: MeshObject, bvh_cache: Dict[str, mathutils.bvhtree.BVHTree],
                            objects_to_check_against: List[MeshObject],
                            list_of_objects_with_no_inside_check: List[MeshObject]):
        """ Checks if a object intersects with any object given in the list.

        The bvh_cache adds all current objects to the bvh tree, which increases the speed.

        If an object is already in the cache it is removed, before performing the check.

        :param obj: Object which should be checked. Type: :class:`bpy.types.Object`
        :param bvh_cache: Dict of all the bvh trees, removes the `obj` from the cache before adding it again. \
                          Type: :class:`dict`
        :param objects_to_check_against: List of objects which the object is checked again \
                                         Type: :class:`list`
        :param list_of_objects_with_no_inside_check: List of objects on which no inside check is performed. \
                                                     This check is only done for the objects in \
                                                     `objects_to_check_against`. Type: :class:`list`
        :return: Type: :class:`bool`, True if no collision was found, false if at least one collision was found
        """

        no_collision = True
        # Now check for collisions
        for collision_obj in objects_to_check_against:
            # Do not check collisions with yourself
            if collision_obj == obj:
                continue
            # First check if bounding boxes collides
            intersection = CollisionUtility.check_bb_intersection(obj, collision_obj)
            # if they do
            if intersection:
                skip_inside_check = collision_obj in list_of_objects_with_no_inside_check
                # then check for more refined collisions
                intersection, bvh_cache = CollisionUtility.check_mesh_intersection(obj, collision_obj, bvh_cache=bvh_cache, skip_inside_check=skip_inside_check)
            if intersection:
                no_collision = False
                break
        return no_collision


    @staticmethod
    def check_bb_intersection(obj1: MeshObject, obj2: MeshObject):
        """
        Checks if there is a bounding box collision, these don't have to be axis-aligned, but if they are not:
        The surrounding/including axis-aligned bounding box is calculated and used to check the intersection.

        :param obj1: object 1  to check for intersection, must be a mesh
        :param obj2: object 2  to check for intersection, must be a mesh
        :return: True if the two bounding boxes intersect with each other
        """
        b1w = obj1.get_bound_box()

        def min_and_max_point(bb):
            """
            Find the minimum and maximum point of the bounding box
            :param bb: bounding box
            :return: min, max
            """
            values = np.array(bb)
            return np.min(values, axis=0), np.max(values, axis=0)

        # get min and max point of the axis-aligned bounding box
        min_b1, max_b1 = min_and_max_point(b1w)
        b2w = obj2.get_bound_box()
        # get min and max point of the axis-aligned bounding box
        min_b2, max_b2 = min_and_max_point(b2w)
        return CollisionUtility.check_bb_intersection_on_values(min_b1, max_b1, min_b2, max_b2)

    @staticmethod
    def check_bb_intersection_on_values(min_b1: list, max_b1: list, min_b2: list, max_b2: list, used_check=lambda a, b: a >= b):
        """
        Checks if there is an intersection of the given bounding box values. Here we use two different bounding boxes,
        namely b1 and b2. Each of them has a corresponding set of min and max values, this works for 2 and 3 dimensional
        problems.

        :param min_b1: List of minimum bounding box points for b1.
        :param max_b1: List of maximum bounding box points for b1.
        :param min_b2: List of minimum bounding box points for b2.
        :param max_b2: List of maximum bounding box points for b2.
        :param used_check: The operation used inside of the is_overlapping1D. With that it possible to change the \
                           collision check from volume and surface check to pure surface or volume checks.
        :return: True if the two bounding boxes intersect with each other
        """
        collide = True
        for min_b1_val, max_b1_val, min_b2_val, max_b2_val in zip(min_b1, max_b1, min_b2, max_b2):
            # inspired by this:
            # https://stackoverflow.com/questions/20925818/algorithm-to-check-if-two-boxes-overlap
            # Checks in each dimension, if there is an overlap if this happens it must be an overlap in 3D, too.
            def is_overlapping_1D(x_min_1, x_max_1, x_min_2, x_max_2):
                # returns true if the min and max values are overlapping
                return used_check(x_max_1, x_min_2) and used_check(x_max_2, x_min_1)

            collide = collide and is_overlapping_1D(min_b1_val, max_b1_val, min_b2_val, max_b2_val)
        return collide

    @staticmethod
    def check_mesh_intersection(obj1: MeshObject, obj2: MeshObject, skip_inside_check: bool = False,
                                bvh_cache: Optional[Dict[str, mathutils.bvhtree.BVHTree]] = None) \
            -> Tuple[bool, Dict[str, mathutils.bvhtree.BVHTree]]:
        """
        Checks if the two objects are intersecting.

        This will use BVH trees to check whether the objects are overlapping.

        It is further also checked if one object is completely inside the other.
        This check requires that both objects are watertight, have correct normals and are coherent.
        If this is not the case it can be disabled via the parameter skip_inside_check.

        :param obj1: object 1 to check for intersection, must be a mesh
        :param obj2: object 2 to check for intersection, must be a mesh
        :param skip_inside_check: Disables checking whether one object is completely inside the other.
        :param bvh_cache: Dict of all the bvh trees, removes the `obj` from the cache before adding it again.
        :return: True, if they are intersecting
        """

        if bvh_cache is None:
            bvh_cache = {}

        # If one of the objects has no vertices, collision is impossible
        if len(obj1.get_mesh().vertices) == 0 or len(obj2.get_mesh().vertices) == 0:
            return False, bvh_cache

        # create bvhtree for obj1
        if obj1.get_name() not in bvh_cache:
            obj1_BVHtree = obj1.create_bvh_tree()
            bvh_cache[obj1.get_name()] = obj1_BVHtree
        else:
            obj1_BVHtree = bvh_cache[obj1.get_name()]

        # create bvhtree for obj2
        if obj2.get_name() not in bvh_cache:
            obj2_BVHtree = obj2.create_bvh_tree()
            bvh_cache[obj2.get_name()] = obj2_BVHtree
        else:
            obj2_BVHtree = bvh_cache[obj2.get_name()]

        # Check whether both meshes intersect
        inter = len(obj1_BVHtree.overlap(obj2_BVHtree)) > 0

        # Optionally check whether obj2 is contained in obj1
        if not inter and not skip_inside_check:
            inter = CollisionUtility.is_point_inside_object(obj1, obj1_BVHtree, Matrix(obj2.get_local2world_mat()) @ obj2.get_mesh().vertices[0].co)
            if inter:
                print("Warning: Detected that " + obj2.get_name() + " is completely inside " + obj1.get_name() +
                      ". This might be wrong, if " + obj1.get_name() +
                      " is not water tight or has incorrect normals. If that is the case, consider setting "
                      "skip_inside_check to True.")

        # Optionally check whether obj1 is contained in obj2
        if not inter and not skip_inside_check:
            inter = CollisionUtility.is_point_inside_object(obj2, obj2_BVHtree, Matrix(obj1.get_local2world_mat()) @ obj1.get_mesh().vertices[0].co)
            if inter:
                print("Warning: Detected that " + obj1.get_name() + " is completely inside " + obj2.get_name() +
                      ". This might be wrong, if " + obj2.get_name() + " is not water tight or has incorrect "
                                                                       "normals. If that is the case, consider "
                                                                       "setting skip_inside_check to True.")

        return inter, bvh_cache

    @staticmethod
    def is_point_inside_object(obj: MeshObject, obj_BVHtree: mathutils.bvhtree.BVHTree, point: Union[Vector, np.ndarray]) -> bool:
        """ Checks whether the given point is inside the given object.

        This only works if the given object is watertight and has correct normals

        :param obj: The object
        :param obj_BVHtree: A bvh tree of the object
        :param point: The point to check
        :return: True, if the point is inside the object
        """
        point = Vector(point)
        # Look for closest point on object
        nearest, normal, _, _ = obj_BVHtree.find_nearest(point)
        # Compute direction
        p2 = nearest - point
        # Compute dot product between direction and normal vector
        a = p2.normalized().dot((Euler(obj.get_rotation()).to_matrix() @ normal).normalized())
        return a >= 0.0
