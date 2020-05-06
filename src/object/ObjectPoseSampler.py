import bpy

from src.utility.BlenderUtility import check_intersection, check_bb_intersection, get_all_mesh_objects
from src.main.Module import Module


class ObjectPoseSampler(Module):
    """ Samples positions and rotations of selected object inside the sampling volume while performing mesh and bounding box collision checks.

    .. csv-table::
       :header: "Parameter", "Description"

       "objects_to_sample", "Here call an appropriate Provider (Getter) in order to select objects. Type: Provider. Optional. Default: all mesh objects."
       "max_tries", "Amount of tries before giving up on an object and moving to the next one. Optional. Type: int. Default value: 1000."
       "pos_sampler", "Here call an appropriate Provider (Sampler) in order to sample position (XYZ 3d vector) for each object. Type: Provider."
       "rot_sampler", "Here call an appropriate Provider (Sampler) in order to sample rotation (Euler angles 3d vector) for each object. Type: Provider."
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """
        Samples positions and rotations of selected object inside the sampling volume while performing mesh and bounding box collision checks in the following steps:
        1. While we have objects remaining and have not run out of tries - sample a point. 
        2. If no collisions are found keep the point.
        """
        # While we have objects remaining and have not run out of tries - sample a point
        # List of successfully placed objects
        placed = []
        # After this many tries we give up on current object and continue with the rest
        max_tries = self.config.get_int("max_iterations", 1000)
        objects = self.config.get_list("objects_to_sample", get_all_mesh_objects())

        # cache to fasten collision detection
        cache = {}

        # for every selected object
        for obj in objects:
            if obj.type == "MESH":

                print("Trying to put ", obj.name)
                prior_location = obj.location
                prior_rotation = obj.rotation_euler
                no_collision = True

                # Try max_iter amount of times
                for i in range(max_tries):

                    # Put the top object in queue at the sampled point in space
                    position = self.config.get_vector3d("pos_sampler")
                    rotation = self.config.get_vector3d("rot_sampler")
                    # assign it a new position
                    obj.location = position
                    # and a rotation
                    obj.rotation_euler = rotation
                    # then update scene
                    bpy.context.view_layer.update()
                    no_collision = True

                    # Now check for collisions
                    for already_placed in placed:
                        # First check if bounding boxes collides
                        intersection = check_bb_intersection(obj, already_placed)
                        # if they do
                        if intersection:
                            # then check for more refined collisions
                            intersection, cache = check_intersection(obj, already_placed)

                        if intersection:
                            no_collision = False
                            break

                    # If no collision then keep the position, else: reset
                    if no_collision:
                        print("No collision detected, moving forward!")
                        placed.append(obj)
                        # then stop trying and keep assigned position and orientation
                        break
                    # if any collisions then reset object to initial state
                    else:
                        print("Collision detected, retrying!!")
                        obj.location = prior_location
                        obj.rotation_euler = prior_rotation 
                        bpy.context.view_layer.update()
                if not no_collision:
                    print("Giving up on ", obj.name)

    def insert_key_frames(self, obj, frame_id):
        """ Insert key frames for given object pose

        :param obj: Loaded object. Type: blender object.
        :param frame_id: The frame number where key frames should be inserted. Type: int.
        """

        obj.keyframe_insert(data_path='location', frame=frame_id)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame_id)
