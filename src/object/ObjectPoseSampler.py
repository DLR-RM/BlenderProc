import bpy
import mathutils

from src.main.Module import Module
from src.utility.BlenderUtility import check_intersection, check_bb_intersection, get_all_blender_mesh_objects


class ObjectPoseSampler(Module):
    """
    Samples positions and rotations of selected object inside the sampling volume while performing mesh and
    bounding box collision checks.

    Example 1: Sample poses (locations and rotations) for objects with a suctom property `sample_pose` set to True.

    .. code-block:: yaml

        {
          "module": "object.ObjectPoseSampler",
          "config":{
            "max_iterations": 1000,
            "objects_to_sample": {
              "provider": "getter.Entity",
              "condition": {
                "cp_sample_pose": True
              }
            },
            "pos_sampler":{
              "provider": "sampler.Uniform3d",
              "max": [5,5,5],
              "min": [-5,-5,-5]
            },
            "rot_sampler": {
              "provider": "sampler.Uniform3d",
              "max": [0,0,0],
              "min": [6.28,6.28,6.28]
            }
          }
        }

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - objects_to_sample
          - Here call an appropriate Provider (Getter) in order to select objects. Default: all mesh objects.
          - Provider
        * - max_iterations
          - Amount of tries before giving up on an object and moving to the next one. Default: 1000.
          - int
        * - pos_sampler
          - Here call an appropriate Provider (Sampler) in order to sample position (XYZ 3d vector) for each object.
            
          - Provider
        * - rot_sampler
          - Here call an appropriate Provider (Sampler) in order to sample rotation (Euler angles 3d vector) for
            each object. 
          - Provider
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """
        Samples positions and rotations of selected object inside the sampling volume while performing mesh and
        bounding box collision checks in the following steps:
        1. While we have objects remaining and have not run out of tries - sample a point. 
        2. If no collisions are found keep the point.
        """
        # While we have objects remaining and have not run out of tries - sample a point
        # List of successfully placed objects
        placed = []
        # After this many tries we give up on current object and continue with the rest
        max_tries = self.config.get_int("max_iterations", 1000)
        objects = self.config.get_list("objects_to_sample", get_all_blender_mesh_objects())

        if max_tries <= 0:
            raise ValueError("The value of max_tries must be greater than zero: {}".format(max_tries))

        if not objects:
            raise Exception("The list of objects can not be empty!")

        # cache to fasten collision detection
        bvh_cache = {}

        # for every selected object
        for obj in objects:
            if obj.type == "MESH":
                no_collision = True

                amount_of_tries_done = -1
                # Try max_iter amount of times
                for i in range(max_tries):

                    # Put the top object in queue at the sampled point in space
                    position = self.config.get_vector3d("pos_sampler")
                    rotation = self.config.get_vector3d("rot_sampler")
                    no_collision = ObjectPoseSampler.check_pose_for_object(obj, position, rotation, bvh_cache,
                                                                           placed, [])

                    # If no collision then keep the position
                    if no_collision:
                        amount_of_tries_done = i
                        break

                if amount_of_tries_done == -1:
                    amount_of_tries_done = max_tries

                placed.append(obj)

                if not no_collision:
                    print("Could not place " + obj.name + " without a collision.")
                else:
                    print("It took " + str(amount_of_tries_done + 1) + " tries to place " + obj.name)

    def insert_key_frames(self, obj, frame_id):
        """ Insert key frames for given object pose

        :param obj: Loaded object. Type: blender object.
        :param frame_id: The frame number where key frames should be inserted. Type: int.
        """

        obj.keyframe_insert(data_path='location', frame=frame_id)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame_id)

    @staticmethod
    def check_pose_for_object(obj: bpy.types.Object, position: mathutils.Vector, rotation: mathutils.Vector,
                              bvh_cache: dict, objects_to_check_against: list,
                              list_of_objects_with_no_inside_check: list):
        """
        Checks if a object placed at the given pose intersects with any object given in the list.

        The bvh_cache adds all current objects to the bvh tree, which increases the speed.

        If an object is already in the cache it is removed, before performing the check.

        :param obj: Object which should be checked. Type: :class:`bpy.types.Object`
        :param position: 3D Vector of the location of the object. Type: :class:`mathutils.Vector`
        :param rotation: 3D Vector of the rotation in euler angles. If this is None, the rotation is not changed \
                         Type: :class:`mathutils.Vector`
        :param bvh_cache: Dict of all the bvh trees, removes the `obj` from the cache before adding it again. \
                          Type: :class:`dict`
        :param objects_to_check_against: List of objects which the object is checked again \
                                         Type: :class:`list`
        :param list_of_objects_with_no_inside_check: List of objects on which no inside check is performed. \
                                                     This check is only done for the objects in \
                                                     `objects_to_check_against`. Type: :class:`list`
        :return: Type: :class:`bool`, True if no collision was found, false if at least one collision was found
        """
        # assign it a new pose
        obj.location = position
        if rotation:
            obj.rotation_euler = rotation
        bpy.context.view_layer.update()
        # Remove bvh cache, as object has changed
        if obj.name in bvh_cache:
            del bvh_cache[obj.name]

        no_collision = True
        # Now check for collisions
        for already_placed in objects_to_check_against:
            # First check if bounding boxes collides
            intersection = check_bb_intersection(obj, already_placed)
            # if they do
            if intersection:
                skip_inside_check = already_placed in list_of_objects_with_no_inside_check
                # then check for more refined collisions
                intersection, bvh_cache = check_intersection(obj, already_placed, bvh_cache=bvh_cache,
                                                             skip_inside_check=skip_inside_check)
            if intersection:
                no_collision = False
                break
        return no_collision
