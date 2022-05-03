import blenderproc as bproc
from pathlib import Path

import argparse
import os
import numpy as np
import random
import time
import bpy
import bpy_extras
import mathutils

from blenderproc.python.utility.Initializer import cleanup
from blenderproc.python.utility.MathUtility import change_source_coordinate_frame_of_transformation_matrix
import csv

parser = argparse.ArgumentParser()
parser.add_argument("output_dir", nargs='?', default="examples/datasets/front_3d_with_improved_mat/output", help="Path to where the data should be saved")
args = parser.parse_args()

bproc.init()

with open('examples/datasets/image_matching/shapenet_verts.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    shapenets = []
    for row in reader:
        shapenets.append((row["type"], row["model_id"], int(row["triangles"])))

shapenets = sorted(shapenets, key=lambda x: x[-1], reverse=True)
shapenet_dir = "/media/domin/data/shapenet/ShapeNetCore.v2/"

Path(os.path.abspath(args.output_dir)).mkdir(exist_ok=True)
shapenet_obj = None
s = 0
for row in shapenets[100:]:
    out = Path(os.path.abspath(args.output_dir)) / (row[1] + ".blend")

    if not out.exists():
        if row[0] in [ "02691156"]:#"02958343",
            continue
        if shapenet_obj is not None:
            shapenet_obj.delete()
        bpy.ops.file.unpack_all()
        cleanup()

        shapenet_obj = bproc.loader.load_shapenet(shapenet_dir, row[0], row[1], move_object_origin=False)
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(out))
        s += 1
        if s == 20:
            break


"""
s = 0
while s < 100:
    cat_id = random.choice(os.listdir(shapenet_dir))
    if cat_id.isdigit():
        shapenet_objs.append(bproc.loader.load_shapenet(shapenet_dir, cat_id, move_object_origin=False))
        s += 1"""

#bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.output_dir))