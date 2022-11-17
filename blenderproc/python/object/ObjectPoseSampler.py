"""Allows the sampling of objects inside a sampling volume, while performing collision checks."""

from typing import Callable, List, Dict, Tuple

import mathutils

from blenderproc.python.utility.CollisionUtility import CollisionUtility
from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.types.MeshObjectUtility import MeshObject, get_all_mesh_objects


def sample_poses(objects_to_sample: List[MeshObject], sample_pose_func: Callable[[MeshObject], None],
                 objects_to_check_collisions: List[MeshObject] = None, max_tries: int = 1000,
                 mode_on_failure: str = "last_pose") -> Dict[Entity, Tuple[int, bool]]:
    """
    Samples positions and rotations of selected object inside the sampling volume while performing mesh and
    bounding box collision checks.


    :param objects_to_sample: A list of mesh objects whose poses are sampled based on the given function.
    :param sample_pose_func: The function to use for sampling the pose of a given object.
    :param objects_to_check_collisions: A list of mesh objects who should not be considered when checking for
                                        collisions.
    :param max_tries: Amount of tries before giving up on an object and moving to the next one.
    :param mode_on_failure: Define final state of objects that could not be placed without collisions within max_tries
                            attempts. Options: 'last_pose', 'initial_pose'

    :return: A dict with the objects to sample as keys and a Tuple with the number of executed attempts to place the
             object as first element, and a bool whether it has been successfully placed without collisions.
    """
    # Check if mode on failure is allowed
    allowed_modes_on_failure = ["last_pose", "initial_pose"]
    if mode_on_failure not in allowed_modes_on_failure:
        raise ValueError(f"{mode_on_failure} is not an allowed mode_on_failure.")

    # After this many tries we give up on current object and continue with the rest
    if objects_to_check_collisions is None:
        objects_to_check_collisions = get_all_mesh_objects()

    # Among objects_to_sample only check collisions against already placed objects
    cur_objects_to_check_collisions = list(set(objects_to_check_collisions) - set(objects_to_sample))

    if max_tries <= 0:
        raise ValueError(f"The value of max_tries must be greater than zero: {max_tries}")

    if not objects_to_sample:
        raise RuntimeError("The list of objects_to_sample can not be empty!")

    # cache to fasten collision detection
    bvh_cache: Dict[str, mathutils.bvhtree.BVHTree] = {}

    sample_results: Dict[Entity, Tuple[int, bool]] = {}

    # for every selected object
    for obj in objects_to_sample:

        # Store the obejct's initial pose in case we need to place it back
        if mode_on_failure == 'initial_pose':
            initial_location = obj.get_location()
            initial_rotation = obj.get_rotation_euler()

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

        if no_collision:
            print(f"It took {amount_of_tries_done + 1} tries to place {obj.get_name()}")
        else:
            amount_of_tries_done = max_tries
            print(f"Could not place {obj.get_name()} without a collision.")

            if mode_on_failure == 'initial_pose':
                obj.set_location(initial_location)
                obj.set_rotation_euler(initial_rotation)

        sample_results[obj] = (amount_of_tries_done, no_collision)

    return sample_results
