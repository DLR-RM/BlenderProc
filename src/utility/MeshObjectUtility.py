from typing import List

import bpy

from src.utility.EntityUtility import Entity
import numpy as np
from mathutils import Vector

class MeshObject(Entity):

    def __init__(self, object: bpy.types.Object):
        super().__init__(object)

    @staticmethod
    def create_from_blender_mesh(blender_mesh: bpy.types.Mesh, object_name: str = None) -> "MeshObject":
        """ Creates a new Mesh object using the given blender mesh.

        :param blender_mesh: The blender mesh.
        :param object_name: The name of the new object. If None is given, the name of the given mesh is used.
        :return: The new Mesh object.
        """
        # link this mesh inside of a new object
        obj = bpy.data.objects.new(blender_mesh.name if object_name is None else object_name, blender_mesh)
        # link the object in the collection
        bpy.context.collection.objects.link(obj)
        return MeshObject(obj)

    @staticmethod
    def create_empty(object_name: str, mesh_name: str = None):
        """ Creates an empty object.

        :param object_name: The name of the new object.
        :param mesh_name: The name of the contained blender mesh. If None is given, the object name is used.
        :return: The new Mesh object.
        """
        if mesh_name is None:
            mesh_name = object_name
        return MeshObject.create_from_blender_mesh(bpy.data.meshes.new(mesh_name), object_name)

    @staticmethod
    def create_primitive(shape: str, **kwargs) -> "MeshObject":
        """ Creates a new primitive mesh object.

        :param shape: The name of the primitive to create. Available: ["CUBE"]
        :return:
        """
        if shape == "CUBE":
            bpy.ops.mesh.primitive_cube_add(*kwargs)
        elif shape == "CYLINDER":
            bpy.ops.mesh.primitive_cylinder_add(*kwargs)
        elif shape == "CONE":
            bpy.ops.mesh.primitive_cone_add(*kwargs)
        elif shape == "PLANE":
            bpy.ops.mesh.primitive_plane_add(*kwargs)
        elif shape == "SPHERE":
            bpy.ops.mesh.primitive_uv_sphere_add(*kwargs)
        elif shape == "MONKEY":
            bpy.ops.mesh.primitive_monkey_add(*kwargs)
        else:
            raise Exception("No such shape: " + shape)

        return MeshObject(bpy.context.object)

    @staticmethod
    def convert_to_meshes(blender_objects: list) -> List["MeshObject"]:
        """ Converts the given list of blender objects to mesh objects
    
        :param blender_objects: List of blender objects.
        :return: The list of meshes.
        """
        return [MeshObject(obj) for obj in blender_objects]

    def get_materials(self) -> List[bpy.types.Material]:
        """ Returns the materials used by the mesh.

        :return: A list of materials.
        """
        return self.blender_obj.data.materials

    def set_material(self, index: int, material: bpy.types.Material):
        """ Sets the given material at the given index of the objects material list.

        :param index: The index to set the material to.
        :param material: The material to set.
        """
        self.blender_obj.data.materials[index] = material

    def add_material(self, material: bpy.types.Material):
        """ Adds a new material to the object.

        :param material: The material to add.
        """
        self.blender_obj.data.materials.append(material)

    def duplicate(self):
        """ Duplicates the object.

        :return: A new mesh object, which is a duplicate of this object.
        """
        new_entity = self.blender_obj.copy()
        new_entity.data = self.blender_obj.data.copy()
        bpy.context.collection.objects.link(new_entity)
        return MeshObject(new_entity)

    def get_mesh(self) -> bpy.types.Mesh:
        """ Returns the blender mesh of the object.

        :return: The mesh.
        """
        return self.blender_obj.data

    def set_shading_mode(self, use_smooth: bool):
        """ Sets the shading mode of all faces of the object.

        :param use_smooth: If true, then all faces will be made smooth, otherwise flat.
        """
        for face in self.get_mesh().polygons:
            face.use_smooth = use_smooth

    def remove_x_axis_rotation(self):
        """
        Removes the 90 degree X-axis rotation found, when loading from `.obj` files. This function rotates the mesh
        itself not just the object, this will set the `rotation_euler` to `[0, 0, 0]`.
        """
        bpy.ops.object.select_all(action='DESELECT')
        # convert object rotation into internal rotation
        self.select()
        bpy.context.view_layer.objects.active = self.blender_obj
        self.set_rotation_euler([0, 0, 0])
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.rotate(value=np.pi * 0.5, orient_axis="X")
        bpy.ops.object.mode_set(mode='OBJECT')
        self.deselect()
        bpy.context.view_layer.update()

    def move_origin_to_bottom_mean_point(self):
        """
        Moves the object center to bottom of the bounding box in Z direction and also in the middle of the X and Y
        plane, which then makes the placement easier.
        """
        bpy.ops.object.select_all(action='DESELECT')
        self.select()
        bpy.context.view_layer.objects.active = self.blender_obj
        bb = self.get_bound_box()
        bb_center = np.mean(bb, axis=0)
        bb_min_z_value = np.min(bb, axis=0)[2]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.translate(value=[-bb_center[0], -bb_center[1], -bb_min_z_value])
        bpy.ops.object.mode_set(mode='OBJECT')
        self.deselect()
        bpy.context.view_layer.update()

    def get_bound_box(self):
        """
        :return: [8x[3xfloat]] the object aligned bounding box coordinates in world coordinates
        """
        return [self.blender_obj.matrix_world @ Vector(cord) for cord in self.blender_obj.bound_box]

    def persist_transformation_into_mesh(self):
        """
        Apply the current transformation of the object, which are saved in the location, scale or rotation attributes
        to the mesh and sets them to their init values.
        """
        bpy.ops.object.select_all(action='DESELECT')
        self.select()
        bpy.context.view_layer.objects.active = self.blender_obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        self.deselect()

