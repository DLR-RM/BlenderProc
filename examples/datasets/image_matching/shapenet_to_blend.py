from blenderproc.python.utility.MathUtility import change_source_coordinate_frame_of_transformation_matrix

import blenderproc as bproc
import argparse
import os
import numpy as np
import random
import time
import bpy
import bpy_extras
import mathutils

parser = argparse.ArgumentParser()
parser.add_argument("output_dir", nargs='?', default="examples/datasets/front_3d_with_improved_mat/output", help="Path to where the data should be saved")
args = parser.parse_args()

bproc.init()

shapenet_objs = []
shapenet_dir = "/media/domin/data/shapenet/ShapeNetCore.v2/"
s = 0
while s < 100:
    cat_id = random.choice(os.listdir(shapenet_dir))
    if cat_id.isdigit():
        shapenet_objs.append(bproc.loader.load_shapenet(shapenet_dir, cat_id, move_object_origin=False))
        s += 1

bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.output_dir))