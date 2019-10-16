from src.main.Module import Module
import bpy
import ast
import mathutils
from math import radians, fabs, acos, degrees
import bmesh

class BoundingBoxLoader(Module):

	def __init__(self, config):
		Module.__init__(self, config)

	def run(self):
		"""Just imports the configured .obj file straight into blender

		The import will load all materials into cycle nodes.
		"""
		if 'mesh' in bpy.data.objects:
			obj = bpy.data.objects['mesh']
			obj.select_set(True)
			bpy.ops.object.mode_set(mode='EDIT')
			mesh = obj.data
			bm = bmesh.from_edit_mesh(mesh)
			up_vec = mathutils.Vector([0,0,1])
			height_list = [-1.54, 1.309]
			counter = 0
			for f in bm.faces:
				f.select = False
				for height_val in height_list:
					if fabs(f.calc_center_median()[2] - height_val) < 0.15:
						if degrees(acos(f.normal @ up_vec)) < 7.5:
							counter += 1
							f.select = True
			print("Selected {} polygons as floor".format(counter))
			bpy.ops.mesh.separate(type='SELECTED')
			bpy.ops.object.mode_set(mode='OBJECT')
			obj.select_set(False)
			bpy.data.objects['mesh.001'].name = 'floor'


		# file_path = self.config.get_string('path')
		# with open(file_path, 'r') as data:
		# 	text = data.read()
		# 	for line in text.split('\n'):
		# 		if len(line) > 0 and 'min' in line:
		# 			current_dict = ast.literal_eval(line)
		# 			current_dict = {key : mathutils.Vector(ast.literal_eval(ele)) for key, ele in current_dict.items()}
		# 			size = (current_dict['max'] - current_dict['min']) * 0.5
		# 			loc = current_dict['min'] + size
		# 			#size = size  - mathutils.Vector([0.5,0.5,0])
		# 			bpy.ops.mesh.primitive_cube_add(location=loc)
		# 			bpy.ops.transform.resize(value=size)
		# 			print(current_dict)

