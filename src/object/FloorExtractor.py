import os
from math import radians, fabs, acos

import bmesh
import bpy
import mathutils

from src.main.Module import Module
from src.utility.Utility import Utility


class FloorExtractor(Module):
    """
    Will search for the specified object and splits the surfaces which point upwards at a specified level away

    Example 1:

    .. code-block:: yaml

        {
          "module": "object.FloorExtractor",
          "config": {
            "is_replica_object": "True",
            "obj_name": "mesh",
            "compare_angle_degrees" : 7.5,
            "compare_height": 0.15
          }
        }

    **Configuration**:
    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - obj_name
          - Name of the object where the floor gets extracted.
          - string
        * - compare_angle_degrees
          - Maximum difference between the up vector and the current polygon normal in degrees. Default: 7.5.
          - float
        * - compare_height
          - Maximum difference in Z direction between the polygons median point and the specified height of the
            room. Default: 0.15.
          - float
        * - is_replica_object
          - In this instance the data_set_name key has to be set. Default: False.
          - bool
        * - height_list_path
          - Path to a file with height values. Specify one if is_replica_object == False.
          - string
        * - data_set_name
          - Name of the data set only useful with replica_dataset.
          - string
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Exctract floors in the following steps:
        1. Searchs for the specified object.
        2. Splits the surfaces which point upwards at a specified level away.
        """
        obj_name = self.config.get_string('obj_name')
        compare_angle = radians(self.config.get_float('compare_angle_degrees', 7.5))
        compare_height = self.config.get_float('compare_height', 0.15)
        if not self.config.get_bool('is_replica_object', False):
            file_path = self.config.get_string('height_list_path')
        else:
            file_folder = os.path.join('resources', 'replica_dataset', 'height_levels', self.config.get_string('data_set_name'))
            file_path = Utility.resolve_path(os.path.join(file_folder, 'height_list_values.txt'))
        with open(file_path) as file:
            import ast
            height_list = [float(val) for val in ast.literal_eval(file.read())]
        for obj in bpy.data.objects:
            obj.select_set(False)
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            mesh = obj.data
            bm = bmesh.from_edit_mesh(mesh)
            up_vec = mathutils.Vector([0,0,1])
            counter = 0
            for f in bm.faces:
                f.select = False
                for height_val in height_list:
                    if fabs(f.calc_center_median()[2] - height_val) < compare_height:
                        if acos(f.normal @ up_vec) < compare_angle:
                            counter += 1
                            f.select = True
            print("Selected {} polygons as floor".format(counter))
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(False)
            bpy.data.objects[obj_name + '.001'].name = 'floor'
