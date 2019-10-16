
from src.main.Module import Module
import bpy
import mathutils
from math import radians, fabs, acos
import bmesh

class FloorExtractor(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """Will search for the specified object and splits the surfaces which point upwards at a specified level away

        """
        obj_name = 'mesh'
        compare_angle = radians(self.config.get_float('compare_angle_degrees', 7.5))
        compare_height = self.config.get_float('compare_height', 0.15)

        file_path = self.config.get_string('height_list_path')
        with open(file_path) as file:
            import ast
            height_list = [float(val) for val in ast.literal_eval(file.read())]
        print(height_list)
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
