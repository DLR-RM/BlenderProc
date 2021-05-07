from typing import List, Union

import bpy

from src.utility.EntityUtility import Entity
import numpy as np
from mathutils import Vector
import bmesh
import mathutils

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
    def create_with_empty_mesh(object_name: str, mesh_name: str = None) -> "MeshObject":
        """ Creates an object with an empty mesh.
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

    def set_shading_mode(self, mode: str, angle_value: float = 30):
        """ Sets the shading mode of all faces of the object.

        :param mode: Desired mode of the shading. Available: ["FLAT", "SMOOTH", "AUTO"]. Type: str
        :param angle_value: Angle in degrees at which flat shading is activated in `AUTO` mode. Type: float
        """
        if mode.lower() == "flat":
            is_smooth = False
            self.blender_obj.data.use_auto_smooth = False
        elif mode.lower() == "smooth":
            is_smooth = True
            self.blender_obj.data.use_auto_smooth = False
        elif mode.lower() == "auto":
            is_smooth = True
            self.blender_obj.data.use_auto_smooth = True
            self.blender_obj.data.auto_smooth_angle = np.deg2rad(angle_value)
        else:
            raise Exception("This shading mode is unknown: {}".format(mode))

        for face in self.get_mesh().polygons:
            face.use_smooth = is_smooth

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

    def persist_transformation_into_mesh(self, location: bool = True, rotation: bool = True, scale: bool = True):
        """
        Apply the current transformation of the object, which are saved in the location, scale or rotation attributes
        to the mesh and sets them to their init values.

        :param location: Determines whether the object's location should be persisted.
        :param rotation: Determines whether the object's rotation should be persisted.
        :param scale: Determines whether the object's scale should be persisted.
        """
        bpy.ops.object.transform_apply({"selected_editable_objects": [self.blender_obj]}, location=location, rotation=rotation, scale=scale)

    def get_origin(self) -> Vector:
        """ Returns the origin of the object.

        :return: The origin in world coordinates.
        """
        return self.blender_obj.location.copy()

    def set_origin(self, point: Union[list, Vector] = None, mode: str = "POINT") -> Vector:
        """ Sets the origin of the object.

        This will not change the appearing pose of the object, as the vertex locations experience the inverse transformation applied to the origin.

        :param point: The point in world coordinates to which the origin should be set. This parameter is only relevent if mode is set to "POINT".
        :param mode: The mode specifying how the origin should be set. Available options are: ["POINT", "CENTER_OF_MASS", "CENTER_OF_VOLUME"]
        :return: The new origin in world coordinates.
        """
        context = {"selected_editable_objects": [self.blender_obj]}

        if mode == "POINT":
            if point is None:
                raise Exception("The parameter point is not given even though the mode is set to POINT.")
            prev_cursor_location = bpy.context.scene.cursor.location
            bpy.context.scene.cursor.location = point
            bpy.ops.object.origin_set(context, type='ORIGIN_CURSOR')
            bpy.context.scene.cursor.location = prev_cursor_location
        elif mode == "CENTER_OF_MASS":
            bpy.ops.object.origin_set(context, type='ORIGIN_CENTER_OF_MASS')
        elif mode == "CENTER_OF_VOLUME":
            bpy.ops.object.origin_set(context, type='ORIGIN_CENTER_OF_VOLUME')
        else:
            raise Exception("No such mode: " + mode)

        return self.get_origin()

    def enable_rigidbody(self, active: bool, collision_shape: str = 'CONVEX_HULL', collision_margin: float = 0.001, collision_mesh_source: str = "FINAL", mass: float = None, mass_factor: float = 1, friction: float = 0.5, angular_damping: float = 0.1, linear_damping: float = 0.04):
        """ Enables the rigidbody component of the object which makes it participate in physics simulations.

        :param active: If True, the object actively participates in the simulation and its key frames are ignored. If False, the object still follows its keyframes and only acts as an obstacle, but is not influenced by the simulation.
        :param collision_shape: Collision shape of object in simulation. Default: 'CONVEX_HULL'. Available: 'BOX', 'SPHERE', 'CAPSULE', 'CYLINDER', 'CONE', 'CONVEX_HULL', 'MESH'.
        :param collision_margin: The margin around objects where collisions are already recognized. Higher values improve stability, but also make objects hover a bit.
        :param collision_mesh_source: Source of the mesh used to create collision shape. Default: 'FINAL'. Available: 'BASE', 'DEFORM', 'FINAL'.
        :param mass: The mass in kilogram the object should have. If None is given the mass is calculated based on its bounding box volume and the given `mass_factor`.
        :param mass_factor: Scaling factor for mass. This is only considered if the given `mass` is None. Defines the linear function mass=bounding_box_volume*mass_factor (defines material density).
        :param friction: Resistance of object to movement.
        :param angular_damping: Amount of angular velocity that is lost over time.
        :param linear_damping: Amount of linear velocity that is lost over time.
        """
        # Enable rigid body component
        bpy.ops.rigidbody.object_add({'object': self.blender_obj})
        # Sett attributes
        rigid_body = self.blender_obj.rigid_body
        rigid_body.type = "ACTIVE" if active else "PASSIVE"
        rigid_body.collision_shape = collision_shape
        rigid_body.collision_margin = collision_margin
        rigid_body.use_margin = True
        rigid_body.mesh_source = collision_mesh_source
        rigid_body.friction = friction
        rigid_body.angular_damping = angular_damping
        rigid_body.linear_damping = linear_damping

        if mass is None:
            rigid_body.mass = self.get_bound_box_volume() * mass_factor
        else:
            rigid_body.mass = mass


    def disable_rigidbody(self):
        """ Disables the rigidbody element of the object """
        bpy.ops.rigidbody.object_remove({'object': self.blender_obj})

    def get_rigidbody(self) -> bpy.types.RigidBodyObject:
        """ Returns the rigid body component

        :return: The rigid body component of the object.
        """
        return self.blender_obj.rigid_body

    def get_bound_box_volume(self) -> float:
        """ Gets the volume of the object aligned bounding box.

        :return: volume of a bounding box.
        """
        bb = self.get_bound_box()
        # Search for the point which is the maximum distance away from the first point
        # we call this first point min and the furthest away point max
        # the vector between the two is a diagonal of the bounding box
        min_point, max_point = bb[0], None
        max_dist = -1
        for point in bb:
            dist = (point - min_point).length
            if dist > max_dist:
                max_point = point
                max_dist = dist
        diag = max_point - min_point
        # use the diagonal to calculate the volume of the box
        return abs(diag[0]) * abs(diag[1]) * abs(diag[2])

    def create_bvh_tree(self) -> mathutils.bvhtree.BVHTree:
        """ Builds a bvh tree based on the object's mesh.

        :return: The new bvh tree
        """
        bm = bmesh.new()
        bm.from_mesh(self.get_mesh())
        bm.transform(self.get_local2world_mat())
        return mathutils.bvhtree.BVHTree.FromBMesh(bm)
