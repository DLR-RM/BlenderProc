import bpy

from src.main.Module import Module
from src.utility.Config import Config


class BasicMeshInitializer(Module):
    """
    """

    def __init__(self, config):
        Module.__init__(self, config)
        #self.name = self.config.get_string("name")
        #self.location = self.config.get_vector3d("location", [0, 0, 0])
        #self.rotation = self.config.get_vector3d("rotation", [0, 0, 0])
        #self.scale = self.config.get_vector3d("scale", [0, 0, 0])

    def run(self):
        """

        :return:
        """
        meshes_to_add = self.config.get_list("add", [])
        for mesh in meshes_to_add:
            mesh_conf = Config(mesh)
            mesh_type = mesh_conf.get_string("type")
            mesh_name = mesh_conf.get_string("name")
            mesh_location = mesh_conf.get_vector3d("location", [0, 0, 0])
            mesh_rotation = mesh_conf.get_vector3d("rotation", [0, 0, 0])
            mesh_scale = mesh_conf.get_vector3d("scale", [1, 1, 1])
            self._add_mesh(mesh_type)
            self._set_attrs(mesh_name, mesh_location, mesh_rotation, mesh_scale)

    def _add_mesh(self, type):
        """

        :param type:
        """
        if type == "plane":
            bpy.ops.mesh.primitive_plane_add()
        elif type == "cube":
            bpy.ops.mesh.primitive_cube_add()
        elif type == "circle":
            bpy.ops.mesh.primitive_circle_add()
        elif type == "uvsphere":
            bpy.ops.mesh.primitive_uv_sphere_add()
        elif type == "icosphere":
            bpy.ops.mesh.primitive_ico_sphere_add()
        elif type == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add()
        elif type == "cone":
            bpy.ops.mesh.primitive_cone_add()
        elif type == "torus":
            bpy.ops.mesh.primitive_torus_add()
        else:
            raise RuntimeError('Unknown basic mesh type "{}"! Available types: "plane", "cube", "circle", "uvsphere", '
                               '"icosphere","cylinder", "cone", "torus".'.format(type))

    def _set_attrs(self, name, location, rotation, scale):
        """

        :param obj:
        :param name:
        :param location:
        :param rotation:
        :param scale:
        :return:
        """
        bpy.context.object.name = name
        bpy.context.object.location = location
        bpy.context.object.rotation_euler = rotation
        bpy.context.object.scale = scale
