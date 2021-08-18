#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 10:53:10 2021

@author: tobiasschmidbaur
"""
import subprocess
import sys
import os
import pathlib
    
# this sets the amount of scenes
amount_of_scenes = 1
# this sets the amount of runs, which are performed
amount_of_runs = 1

# set the folder in which the run.py is located
rerun_folder = os.path.abspath(os.path.dirname(__file__))

# the first one is the rerun.py script, the last is the output
used_arguments = sys.argv[1:-1]
config_file, blend_file = used_arguments
output_location = os.path.abspath(sys.argv[-1])

for scene_id in range(amount_of_scenes):
    for run_id in range(amount_of_runs):
        # in each run, the arguments are reused
        cmd = ["python3", os.path.join(rerun_folder, "run.py")]
        cmd.append(config_file)
        cmd.append(blend_file)
        # the only exception is the output, which gets changed for each run, so that the examples are not overwritten
        #cmd.append(os.path.join(output_location, str(run_id)))
        cmd.append(output_location)
        print(" ".join(cmd))
        # execute one BlenderProc run
        subprocess.call(" ".join(cmd), shell=True)
        
    #get the blend file 
    old_blend_file = str(scene_id) + ".blend"
    new_blend_file = str(scene_id + 1) + ".blend"
    blend_file = str(pathlib.Path(str(blend_file).replace(old_blend_file, new_blend_file)))






