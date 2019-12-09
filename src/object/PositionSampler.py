from src.utility.BlenderUtility import check_intersection, check_bb_intersection
import mathutils
from math import pi
import bpy
from random import uniform
from src.utility.Utility import Utility
from src.main.Module import Module


class PositionSampler(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ 
        For each object,
            1- Place the object outside sampling volume
            2- Until we have objects remaining and have not run out of tries, Sample a point
            3- Put the top object in queue at the sampled point
            4- If no collision then keep the position else reset
        Here we use any general sampling method supported by us
        """
        pos_sampler_params = self.config.get_raw_dict("pos_sampler")    
        rot_sampler_params = self.config.get_raw_dict("rot_sampler")

        # 2- Until we have objects remaining and have not run out of tries, Sample a point
        placed = [] # List of objects successfully placed
        max_tries = self.config.get_int("max_iterations", 1000)   # After this many tries we give up on current object and continue with rest
        cache = {} # cache to fasten collision detection
        for obj in bpy.context.scene.objects: # for each object
            if obj.type == "MESH":
                print("Trying to put ", obj.name)
                prior_location = obj.location
                prior_rotation = obj.rotation_euler
                no_collision = True
                for i in range(max_tries): # Try max_iter amount of times
                    # 3- Put the top object in queue at the sampled point in space
                    position = Utility.sample_based_on_config(pos_sampler_params) 
                    rotation = Utility.sample_based_on_config(rot_sampler_params) 
                    obj.location = position # assign it a new position
                    obj.rotation_euler = rotation # and a rotation
                    bpy.context.view_layer.update() # then udpate scene
                    no_collision = True
                    for already_placed in placed: # Now check for collisions
                        intersection  = check_bb_intersection(obj,already_placed) # First check if bounding boxes collides
                        if intersection: # if they do
                            intersection, cache = check_intersection(obj,already_placed) # then check for more refined collisions
                        if intersection:
                            no_collision = False
                            break
                    # 4- If no collision then keep the position else reset
                    if no_collision: # if no collisions
                        print("No collision detected, Moving forward!") 
                        placed.append(obj)
                        break # then stop trying and keep assigned position and orientation
                    else: # if any collisions then reset object to initial state
                        print("collision detected, Retrying!!") 
                        obj.location = prior_location
                        obj.rotation_euler = prior_rotation 
                        bpy.context.view_layer.update()
                if not no_collision:
                    print("giving up on ",obj.name)



            


