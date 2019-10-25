from src.utility.Blender import check_intersection, check_bb_intersection
import mathutils
from math import pi
import bpy
from random import uniform
from src.utility.Utility import Utility
from src.main.Module import Module
import time

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
        start = time.time()
        bad_position = (10000,10000,10000) # for now just assuming that this will always be outside our sampling space

        # 1- Place the object outside sampling volume
        for obj in bpy.context.scene.objects:
            obj.location = bad_position
        bpy.context.view_layer.update()

        # initialize the sampler (This will change, just an example sampler to make the code work)
        class CubeSampler:
            def __init__(self,_min,_max):
                self.min = _min
                self.max = _max
            def get_sample(self):
                x = uniform(self.min[0], self.max[0])
                y = uniform(self.min[1], self.max[1])
                z = uniform(self.min[2], self.max[2])
                return (x,y,z)
        
        # All of sampler configs will be handled more elaborately when we have the general sampler class
        # Please refer to https://rmc-github.robotic.dlr.de/denn-ma/BlenderProc/issues/106
        pos_sampler_type = self.config.get_string("pos_sampler/type")
        pos_sampler_params = self.config.get_raw_dict("pos_sampler/params") # this will evantually be passed to the generic sampler class

        if pos_sampler_type is None:
            raise Exception("Missing sampler type")

        if pos_sampler_params is None:
            raise Exception("Missing sampler params")

        # since for now we only have one sampler for position sampling, we hardcode the method to extract
        # params required by this sampler which are triplets of min and max
        pos_min = self.config.get_list("pos_sampler/params/min",size=3)
        pos_max = self.config.get_list("pos_sampler/params/max",size=3)
        
        # similarly a naive rotation sampler, this can change in future
        rot_sampler_type = self.config.get_string("rot_sampler/type")
        rot_sampler_params = self.config.get_raw_dict("rot_sampler/params") # this will evantually be passed to the generic sampler class

        if rot_sampler_type is None:
            raise Exception("Missing sampler type")

        if rot_sampler_params is None:
            raise Exception("Missing sampler params")
        
        # since for now we only have one sampler for rotation sampling, we hardcode the method to extract
        # params required by this sampler which are triplets of min and max
        rot_min = self.config.get_list("rot_sampler/params/min",size=3)
        rot_max = self.config.get_list("rot_sampler/params/max",size=3)

        pos_sampler = CubeSampler(pos_min,pos_max)
        rad_sampler = CubeSampler(rot_min,rot_max)

        # 2- Until we have objects remaining and have not run out of tries, Sample a point
        placed = [] # List of objects successfully placed
        max_tries = 1000 # After this many tries we give up on current object and continue with rest
        cache = {} # cache to fasten collision detection
        for obj in bpy.context.scene.objects: # for each object
            if obj.type == "MESH":
                print("Trying to put ", obj.name)
                prior_location = obj.location
                prior_rotation = obj.rotation_euler
                no_collision = True
                for i in range(max_tries): # Try max_iter amount of times
                    # 3- Put the top object in queue at the sampled point in space
                    position = pos_sampler.get_sample() 
                    rotation = rad_sampler.get_sample()
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
        print("=====>> Time spent in position sampling ",time.time() - start)



            


