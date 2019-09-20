import json
import os
from mathutils import Matrix, Vector, Euler
import math
import csv

from src.main.Module import Module
from src.utility.Utility import Utility
import bpy

class BopLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """TODO: Load Bop toolkit params
        gt.json, info.json
        1. render test scenes and compare
        2. render random poses in params range
        3. render in front of random backgrounds
        
        """
        bpy.ops.import_mesh.ply(filepath=self.config.get_string("path"))
        
        # Create 
        mat_rot = Matrix.Rotation(math.radians(90.0), 4, 'X')
        mat_trans = Matrix.Translation(Vector((1.0, 2.0, 3.0)))
        mat_sca = Matrix.Scale(0.001, 4)

        transform = mat_trans @ mat_rot @ mat_sca
        for object in bpy.context.selected_objects:
            object.matrix_world @= transform



    