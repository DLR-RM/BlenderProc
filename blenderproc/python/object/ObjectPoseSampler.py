from typing import Callable, List, Dict

import mathutils

from blenderproc.python.utility.CollisionUtility import CollisionUtility
from blenderproc.python.types.MeshObjectUtility import MeshObject, get_all_mesh_objects


def sample_poses(objects_to_sample: List[MeshObject], sample_pose_func: Callable[[MeshObject], None],
                 objects_to_check_collisions: List[MeshObject] = None, max_tries: int = 1000):
    """ Samples positions and rotations of selected object inside the sampling volume while performing mesh and bounding box collision checks.

    :param objects_to_sample: A list of mesh objects whose poses are sampled based on the given function.
    :param sample_pose_func: The function to use for sampling the pose of a given object.
    :param objects_to_check_collisions: A list of mesh objects who should not be considered when checking for collisions.
    :param max_tries: Amount of tries before giving up on an object and moving to the next one.
    """
    # After this many tries we give up on current object and continue with the rest
    if objects_to_check_collisions is None:
        objects_to_check_collisions = get_all_mesh_objects()

    # Among objects_to_sample only check collisions against already placed objects
    cur_objects_to_check_collisions = list(set(objects_to_check_collisions) - set(objects_to_sample))

    if max_tries <= 0:
        raise ValueError("The value of max_tries must be greater than zero: {}".format(max_tries))

    if not objects_to_sample:
        raise Exception("The list of objects_to_sample can not be empty!")

    # cache to fasten collision detection
    bvh_cache: Dict[str, mathutils.bvhtree.BVHTree] = {}

    # for every selected object
    for obj in objects_to_sample:
        no_collision = True

        amount_of_tries_done = -1

        # Try max_iter amount of times
        for i in range(max_tries):

            # Put the top object in queue at the sampled point in space
            sample_pose_func(obj)
            # Remove bvh cache, as object has changed
            if obj.get_name() in bvh_cache:
                del bvh_cache[obj.get_name()]

            no_collision = CollisionUtility.check_intersections(obj, bvh_cache, cur_objects_to_check_collisions, [])

            # If no collision then keep the position
            if no_collision:
                amount_of_tries_done = i
                break

        # After placing an object, we will check collisions with it
        cur_objects_to_check_collisions.append(obj)

        if amount_of_tries_done == -1:
            amount_of_tries_done = max_tries

        if not no_collision:
            print("Could not place " + obj.get_name() + " without a collision.")
        else:
            print("It took " + str(amount_of_tries_done + 1) + " tries to place " + obj.get_name())
