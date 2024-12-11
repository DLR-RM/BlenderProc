""" All mesh objects are captured in this class. """

from typing import List, Union, Tuple, Optional
from sys import platform
from pathlib import Path

import warnings
import bpy
import numpy as np
import bmesh
import mathutils
from mathutils import Vector, Matrix
from trimesh import Trimesh

from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.utility.Utility import Utility, resolve_path
from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects
from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.material import MaterialLoaderUtility
from blenderproc.python.utility.SetupUtility import SetupUtility

if platform != "win32":
    # this is only supported under linux and macOS, the import itself already doesn't work under windows
    from blenderproc.external.vhacd.decompose import convex_decomposition


class MeshObject(Entity):
    """
    Every instance of this class is a mesh which can be rendered in the scene. It can have multiple materials and
    different configurations of vertices with faces and edges.
    """
    def materials(self) -> int:
        """ Returns the number of material slots of the object.

        :return: The number of material slots.
        """
        return len(self.blender_obj.material_slots)

    def get_material_slot_link(self, index: int) -> str:
        """ Returns whether object's or object's data material is used in the material slot.

        :return: "DATA" if the material slot is linked to data material or "OBJECT" otherwise.
        """
        return self.blender_obj.material_slots[index].link

    def set_material_slot_link(self, index: int, link: str):
        """ Sets whether object's or object's data material is used in the material slot.
        Available: ["DATA", "OBJECT"]. Type: str
        """
        self.blender_obj.material_slots[index].link = link

    def get_material(self, index: int, link = "VISIBLE") -> Material:
        """ Returns the material used by the object.

        :link: The mode specifying whether to get material linked to the object or object's data.
        Available: ["DATA", "OBJECT", "VISIBLE"]. Type: str
        :return: A list of materials.
        """
        link = link.upper()
        if link == "VISIBLE" and self.get_material_slot_link(index) == "DATA":
            link = "DATA"
        link2get = "OBJECT" if link == "VISIBLE" else link

        link2return = self.get_material_slot_link(index)
        self.set_material_slot_link(index, link2get)
        material = self.blender_obj.material_slots[index].material
        self.set_material_slot_link(index, link2return)

        # If there is no material in the `OBJECT` slot then the 'DATA' material is displayed.
        if material is None and link == "VISIBLE":
            return self.get_material(index, "DATA")
        else:
            return MaterialLoaderUtility.convert_to_material(material)

    def get_materials(self, link = "VISIBLE") -> List[Optional[Material]]:
        """ Returns the materials used by the object.

        :link: The mode specifying whether to get materials linked to the object or object's data.
        Available: ["DATA", "OBJECT", "VISIBLE"]. Type: str
        :return: A list of materials.
        """
        return [self.get_material(index, link) for index in range(self.materials())]

    def has_materials(self) -> bool:
        """
        Returns True if the object has material slots. This does not necessarily mean any `Material` is assigned to it.

        :return: True if the object has material slots.
        """
        return self.materials() > 0

    def set_material(self, index: int, material: Material, link="DATA"):
        """ Sets the given material at the given index of the object's material list.

        :param index: The index to set the material to.
        :param material: The material to set.
        :link: The mode specifying whether to link material to the object or object's data.
               Available: ["DATA", "OBJECT"]. Type: str
        """
        keep_link = self.get_material_slot_link(index)
        self.set_material_slot_link(index, link)
        self.blender_obj.material_slots[index].material = None if material is None else material.blender_obj
        self.set_material_slot_link(index, keep_link)

    def add_material(self, material: Material):
        """ Adds a new material to the object's data.

        :param material: The material to add.
        """
        self.blender_obj.data.materials.append(material.blender_obj)

    def new_material(self, name: str) -> Material:
        """ Creates a new material and adds it to the object's data.

        :param name: The name of the new material.
        """
        new_mat = MaterialLoaderUtility.create(name)
        self.add_material(new_mat)
        return new_mat

    def clear_materials(self):
        """ Removes all materials from the object's data. """
        self.blender_obj.data.materials.clear()

    def replace_materials(self, material: bpy.types.Material):
        """ Replaces all materials of the object's data with the given new material.

        :param material: A material that should exclusively be used as new material for the object.
        """
        # first remove all existing
        self.clear_materials()
        # add the new one
        self.add_material(material)

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
        elif mode.lower() == "smooth":
            is_smooth = True
        elif mode.lower() == "auto":
            is_smooth = True
            self.add_auto_smooth_modifier(angle=angle_value)
        else:
            raise RuntimeError(f"This shading mode is unknown: {mode}")

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
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.translate(value=[-bb_center[0], -bb_center[1], -bb_min_z_value])
        bpy.ops.object.mode_set(mode='OBJECT')
        self.deselect()

    def get_bound_box(self, local_coords: bool = False) -> np.ndarray:
        """
        :return: 8x3 array describing the object aligned bounding box coordinates in world coordinates
        """
        if not local_coords:
            local2world = Matrix(self.get_local2world_mat())
            return np.array([local2world @ Vector(cord) for cord in self.blender_obj.bound_box])
        return np.array([Vector(cord) for cord in self.blender_obj.bound_box])

    def persist_transformation_into_mesh(self, location: bool = True, rotation: bool = True, scale: bool = True):
        """
        Apply the current transformation of the object, which are saved in the location, scale or rotation attributes
        to the mesh and sets them to their init values.

        :param location: Determines whether the object's location should be persisted.
        :param rotation: Determines whether the object's rotation should be persisted.
        :param scale: Determines whether the object's scale should be persisted.
        """
        with bpy.context.temp_override(selected_editable_objects=[self.blender_obj]):
            bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)

    def get_origin(self) -> np.ndarray:
        """ Returns the origin of the object.

        :return: The origin in world coordinates.
        """
        return np.array(self.blender_obj.location.copy())

    def set_origin(self, point: Union[list, np.ndarray, Vector] = None, mode: str = "POINT") -> np.ndarray:
        """ Sets the origin of the object.

        This will not change the appearing pose of the object, as the vertex locations experience the inverse
        transformation applied to the origin.

        :param point: The point in world coordinates to which the origin should be set. This parameter is only
                      relevant if mode is set to "POINT".
        :param mode: The mode specifying how the origin should be set. Available options are: ["POINT",
                     "CENTER_OF_MASS", "CENTER_OF_VOLUME"]
        :return: The new origin in world coordinates.
        """
        with bpy.context.temp_override(selected_editable_objects=[self.blender_obj]):
            if mode == "POINT":
                if point is None:
                    raise Exception("The parameter point is not given even though the mode is set to POINT.")
                prev_cursor_location = bpy.context.scene.cursor.location.copy()
                bpy.context.scene.cursor.location = point
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                bpy.context.scene.cursor.location = prev_cursor_location.copy()
            elif mode == "CENTER_OF_MASS":
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
            elif mode == "CENTER_OF_VOLUME":
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
            else:
                raise Exception("No such mode: " + mode)

        return self.get_origin()

    def enable_rigidbody(self, active: bool, collision_shape: str = 'CONVEX_HULL', collision_margin: float = 0.001,
                         collision_mesh_source: str = "FINAL", mass: Optional[float] = None, mass_factor: float = 1,
                         friction: float = 0.5, angular_damping: float = 0.1, linear_damping: float = 0.04):
        """ Enables the rigidbody component of the object which makes it participate in physics simulations.

        :param active: If True, the object actively participates in the simulation and its key frames are ignored.
                       If False, the object still follows its keyframes and only acts as an obstacle, but is not
                       influenced by the simulation.
        :param collision_shape: Collision shape of object in simulation. Default: 'CONVEX_HULL'. Available: 'BOX',
                                'SPHERE', 'CAPSULE', 'CYLINDER', 'CONE', 'CONVEX_HULL', 'MESH', 'COMPOUND'.
        :param collision_margin: The margin around objects where collisions are already recognized. Higher values
                                 improve stability, but also make objects hover a bit.
        :param collision_mesh_source: Source of the mesh used to create collision shape. Default: 'FINAL'. Available:
                                      ['BASE', 'DEFORM', 'FINAL'].
        :param mass: The mass in kilogram the object should have. If None is given the mass is calculated based on
                     its bounding box volume and the given `mass_factor`.
        :param mass_factor: Scaling factor for mass. This is only considered if the given `mass` is None. Defines the
                            linear function mass=bounding_box_volume*mass_factor (defines material density).
        :param friction: Resistance of object to movement.
        :param angular_damping: Amount of angular velocity that is lost over time.
        :param linear_damping: Amount of linear velocity that is lost over time.
        """
        # Enable rigid body component
        with bpy.context.temp_override(object=self.blender_obj):
            bpy.ops.rigidbody.object_add()
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

    def build_convex_decomposition_collision_shape(self, vhacd_path: str, temp_dir: Optional[str] = None,
                                                   cache_dir: str = "blenderproc_resources/decomposition_cache"):
        """ Builds a collision shape of the object by decomposing it into near convex parts using V-HACD

        :param vhacd_path: The directory in which vhacd should be installed or is already installed.
        :param temp_dir: The temp dir to use for storing the object files created by v-hacd.
        :param cache_dir: If a directory is given, convex decompositions are stored there named after the meshes hash.
                          If the same mesh is decomposed a second time, the result is loaded from the cache and the
                          actual decomposition is skipped.
        """
        if platform == "win32":
            raise Exception("This is currently not supported under Windows")

        if temp_dir is None:
            temp_dir = Utility.get_temporary_directory()

        # Decompose the object
        parts = convex_decomposition(self, temp_dir, resolve_path(vhacd_path), cache_dir=resolve_path(cache_dir))
        parts = [MeshObject(p) for p in parts]

        # Make the convex parts children of this object, enable their rigid body component and hide them
        for part in parts:
            part.set_parent(self)
            part.enable_rigidbody(True, "CONVEX_HULL")
            part.hide()

    def disable_rigidbody(self):
        """ Disables the rigidbody element of the object """
        if self.has_rigidbody_enabled():
            with bpy.context.temp_override(object=self.blender_obj):
                bpy.ops.rigidbody.object_remove()
        else:
            warnings.warn(f"MeshObject {self.get_name()} has no rigid_body component enabled")

    def has_rigidbody_enabled(self) -> bool:
        """ Checks whether object has rigidbody element enabled

        :return: True if object has rigidbody element enabled
        """
        return self.get_rigidbody() is not None

    def get_rigidbody(self) -> Optional[bpy.types.RigidBodyObject]:
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
            dist = np.linalg.norm(point - min_point)
            if dist > max_dist:
                max_point = point
                max_dist = dist
        diag = max_point - min_point
        # use the diagonal to calculate the volume of the box
        return abs(diag[0]) * abs(diag[1]) * abs(diag[2])

    def mesh_as_bmesh(self, return_copy=False) -> bmesh.types.BMesh:
        """ Returns a bmesh based on the object's mesh.

        Independent of return_copy, changes to the returned bmesh only take into effect after calling
        update_from_bmesh().

        :param return_copy: If True, a copy of the objects bmesh will be returned, otherwise the bmesh owned by
                            blender is returned (the object has to be in edit mode for that).
        :return: The bmesh
        """
        if return_copy:
            bm = bmesh.new()
            bm.from_mesh(self.get_mesh())
        else:
            if bpy.context.mode != "EDIT_MESH":
                raise Exception(f"The object: {self.get_name()} is not in EDIT mode before calling mesh_as_bmesh()")
            bm = bmesh.from_edit_mesh(self.get_mesh())
        return bm

    def update_from_bmesh(self, bm: bmesh.types.BMesh, free_bm_mesh=True) -> bmesh.types.BMesh:
        """ Updates the object's mesh based on the given bmesh.

        :param bm: The bmesh to set.
        :param free_bm_mesh: If True and the given bmesh is not owned by blender, it will be deleted in the end.
        """
        # If the bmesh is owned by blender
        if bm.is_wrapped:
            # Just tell the mesh to update itself based on its bmesh
            bmesh.update_edit_mesh(self.get_mesh())
        else:
            # Set mesh from bmesh
            bm.to_mesh(self.get_mesh())
            # Optional: Free the bmesh
            if free_bm_mesh:
                bm.free()
        # Make sure the mesh is updated
        self.get_mesh().update()

    def join_with_other_objects(self, objects: List["MeshObject"]):
        """
            Joins the given list of objects with this object.

            Does not change the global selection.
            The given object-references become invalid after the join operation.

        :param objects: List of objects which will be merged with this object
        """
        context = {}
        context["object"] = context["active_object"] = self.blender_obj
        # save selection
        # select all objects which will be merged with the target
        context["selected_objects"] = context["selected_editable_objects"] = [obj.blender_obj for obj in objects] + \
                                                                             [self.blender_obj]
        with bpy.context.temp_override(**context):
            # execute the joining operation
            bpy.ops.object.join()

    def edit_mode(self):
        """ Switch into edit mode of this mesh object """
        # Make sure we are in object mode
        if bpy.context.mode != "OBJECT":
            self.object_mode()

        # Set object active (Context overriding does not work for bpy.ops.object.mode_set)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = self.blender_obj
        self.blender_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

    def object_mode(self):
        """ Switch back into object mode """
        bpy.ops.object.mode_set(mode='OBJECT')

    def create_bvh_tree(self) -> mathutils.bvhtree.BVHTree:
        """ Builds a bvh tree based on the object's mesh.

        :return: The new bvh tree
        """
        bm = bmesh.new()
        bm.from_mesh(self.get_mesh())
        bm.transform(Matrix(self.get_local2world_mat()))
        bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
        bm.free()
        return bvh_tree

    def position_is_above_object(self, position: Union[Vector, np.ndarray],
                                 down_direction: Union[Vector, np.ndarray] = None, check_no_objects_in_between=True):
        """ Make sure the given position is straight above the given object.

        If check_no_objects_in_between is True, this also checks that there are no other objects in between.

        :param position: The position to check.
        :param down_direction: A vector specifying the direction straight down. If None is given, a vector
                               into -Z direction is used.
        :param check_no_objects_in_between: If True, it is also checked that no other objects are in between
                                            position and object.
        :return: True, if a ray sent into negative z-direction starting from the position hits the object first.
        """
        if down_direction is None:
            down_direction = [0, 0, -1]

        if check_no_objects_in_between:
            # Send a ray straight down and check if the first hit object is the query object
            hit, _, _, _, hit_object, _ = scene_ray_cast(position, down_direction)
            return hit and hit_object == self
        # Compute world-to-local matrix, so we can bring position and down vector into the local coordinate system
        world2local = Matrix(np.linalg.inv(self.get_local2world_mat()))
        # Send raycast on object (this will ignore all other objects, so we only need to check whether the ray hit)
        hit, _, _, _ = self.blender_obj.ray_cast(world2local @ Vector(position),
                                                 world2local.to_3x3() @ Vector(down_direction))
        return hit

    def ray_cast(self, origin: Union[Vector, list, np.ndarray], direction: Union[Vector, list, np.ndarray],
                 max_distance: float = 1.70141e+38) -> Tuple[bool, np.ndarray, np.ndarray, int]:
        """ Cast a ray onto evaluated geometry, in object space.

        :param origin: Origin of the ray, in object space.
        :param direction: Direction of the ray, in object space.
        :param max_distance: Maximum distance.
        :return: Whether the ray successfully hit the geometry
                 The hit location of this ray cast, float array of 3 items in [-inf, inf]
                 The face normal at the ray cast hit location, float array of 3 items in [-inf, inf]
                 The face index, -1 when original data isn’t available, int in [-inf, inf]
        """
        result, location, normal, index = self.blender_obj.ray_cast(Vector(origin), Vector(direction),
                                                                    distance=max_distance)
        return result, np.array(location), np.array(normal), index

    def add_uv_mapping(self, projection: str, overwrite: bool = False):
        """ Adds a UV mapping to the object based on the given projection type.

        :param projection: The kind of projection to use. Available: ["cube, "cylinder", "smart", "sphere"].
        :param overwrite: If True, the uv mapping will be changed, even if the object already has an uv mapping.
        """
        if not self.has_uv_mapping() or overwrite:
            self.edit_mode()
            bpy.ops.mesh.select_all(action='SELECT')
            if projection == "cube":
                bpy.ops.uv.cube_project()
            elif projection == "cylinder":
                bpy.ops.uv.cylinder_project()
            elif projection == "smart":
                bpy.ops.uv.smart_project()
            elif projection == "sphere":
                bpy.ops.uv.sphere_project()
            else:
                raise RuntimeError(f"Unknown projection: '{projection}'. Please use 'cube', 'cylinder', "
                                   f"'smart' or 'sphere'.")
            self.object_mode()

    def has_uv_mapping(self):
        """ Returns whether the mesh object has a valid uv mapping. """
        if len(self.blender_obj.data.uv_layers) > 1:
            raise Exception("This only support objects which only have one uv layer.")
        for layer in self.blender_obj.data.uv_layers:
            max_val = np.max([list(uv_coords.uv) for uv_coords in layer.data])
            return max_val > 1e-7
        return False

    def scale_uv_coordinates(self, factor: float):
        """Scales the UV coordinates of an object by a given factor. Scaling with a factor greater than one has the
        effect of making the texture look smaller on the object.

        :param factor: The amount the UV coordinates will be scaled.
        :type factor: float
        """
        if not self.has_uv_mapping():
            raise Exception("Cannot scale UV coordinates of a MeshObject that has no UV mapping.")

        mesh = self.blender_obj.data
        uv_layer = mesh.uv_layers.active
        for loop in mesh.loops:
            uv_layer.data[loop.index].uv *= factor

    def add_displace_modifier(self, texture: bpy.types.Texture, mid_level: float = 0.5, strength: float = 0.1,
                              min_vertices_for_subdiv: int = 10000, subdiv_level: int = 2):
        """ Adds a displace modifier with a texture to an object.

        If the mesh has less than min_vertices_for_subdiv vertices, also a subdivision modifier is added.

        :param texture: The texture that will be used to displace the vertices.
        :param mid_level: Texture value that gives no displacement. Parameter of displace modifier.
        :param strength: Amount to displace geometry. Parameter of displace modifier.
        :param min_vertices_for_subdiv: Checks if a subdivision is necessary. If the vertices of a object are less than
                                        'min_vertices_for_subdiv' a Subdivision modifier will be add to the object.
        :param subdiv_level:  Numbers of Subdivisions to perform when rendering. Parameter of Subdivision modifier.
        """
        # Add a subdivision modifier, if the mesh has too less vertices.
        if not len(self.get_mesh().vertices) > min_vertices_for_subdiv:
            self.add_modifier("SUBSURF", render_levels=subdiv_level)

        # Add the displacement modifier
        self.add_modifier("DISPLACE", texture=texture, mid_level=mid_level, strength=strength)

    def add_modifier(self, name: str, **kwargs):
        """ Adds a new modifier to the object.

        :param name: The name/type of the modifier to add.
        :param kwargs: Additional attributes that should be set to the modifier.
        """
        # Create the new modifier
        with bpy.context.temp_override(object=self.blender_obj):
            bpy.ops.object.modifier_add(type=name)

        # Set the attributes
        modifier = self.blender_obj.modifiers[-1]
        for key, value in kwargs.items():
            setattr(modifier, key, value)

    def add_geometry_nodes(self):
        """ Adds a new geometry nodes modifier to the object.
        """
        # Create the new modifier
        with bpy.context.temp_override(object=self.blender_obj):
            bpy.ops.node.new_geometry_nodes_modifier()
        modifier = self.blender_obj.modifiers[-1]
        return modifier.node_group

    def add_auto_smooth_modifier(self, angle: float = 30.0):
        """ Adds the 'Smooth by Angle' geometry nodes modifier.
        
        This replaces the 'Auto Smooth' behavior available in Blender before 4.1.

        :param angle: Maximum angle (in degrees) between face normals that will be considered as smooth.
        """
        # The bpy.ops.object.modifier_add_node_group doesn't work in background mode :( 
        # So we load the node group and create the modifier ourselves.
        # Known issue: https://projects.blender.org/blender/blender/issues/117399

        # The datafiles are expected to be in the same folder relative to blender's python binary.
        python_bin = SetupUtility.determine_python_paths(None, None)[0]
        path = Path(python_bin).parent.parent.parent / "datafiles" / "assets" / "geometry_nodes" / "smooth_by_angle.blend"
        if not path.exists():
            raise RuntimeError(f"Could not find the path to the 'ESSENTIALS' asset folder expected at {path}")
        
        # Get the node group from the current file (reuse if it exists), otherwise load it from the
        # precalculated path and append to the current .blend.
        smooth_by_angle_node_group_name = "Smooth by Angle"
        existing_node_group = bpy.data.node_groups.get(smooth_by_angle_node_group_name, None)
        if existing_node_group is None:
            with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
                data_to.node_groups = [smooth_by_angle_node_group_name]
            existing_node_group = data_to.node_groups[0]

        # Check if the modifier already exists
        modifier = None
        for existing_mod in self.blender_obj.modifiers:
            if existing_mod.type == 'NODES' and existing_mod.node_group == existing_node_group:
                modifier = modifier
                break
        
        # Create a new modifier if no existing modifier was found
        if modifier is None:
            modifier = self.blender_obj.modifiers.new(name=smooth_by_angle_node_group_name, type='NODES')
            modifier.node_group = existing_node_group

        modifier = self.blender_obj.modifiers["Smooth by Angle"]
        modifier["Input_1"] = np.deg2rad(float(angle))

    def mesh_as_trimesh(self) -> Trimesh:
         """ Returns a trimesh.Trimesh instance of the MeshObject.
    
         :return: The object as trimesh.Trimesh.
         """
    
         # get mesh data
         mesh = self.get_mesh()
         
         # check if faces are pure tris or quads and triangulate quads if this is not the case
         if not all(len(f.vertices[:]) == len(mesh.polygons[0].vertices[:]) for f in mesh.polygons):
             # Triangulate quads
             self.select()
             bpy.ops.object.mode_set(mode='EDIT')
             bpy.ops.mesh.select_all(action='SELECT')
             bpy.ops.mesh.quads_convert_to_tris(quad_method='FIXED', ngon_method='BEAUTY') 
             bpy.ops.object.mode_set(mode='OBJECT')
             self.deselect()
         
         # get vertices 
         verts = np.array([[v.co[0], v.co[1], v.co[2]] for v in mesh.vertices])
         # re-scale the vertices since scale operations doesn't apply to the mesh data
         verts *= self.blender_obj.scale
         # get faces   
         faces = np.array([f.vertices[:] for f in mesh.polygons if len(f.vertices[:]) in [3, 4]])
    
         return Trimesh(vertices=verts, faces=faces)

    def clear_custom_splitnormals(self) -> None:
        """ Removes custom split normals which might exist after importing the object from file. """

        with bpy.context.temp_override(object=self.blender_obj):
            bpy.ops.mesh.customdata_custom_splitnormals_clear()

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


def create_with_empty_mesh(object_name: str, mesh_name: str = None) -> "MeshObject":
    """ Creates an object with an empty mesh.
    :param object_name: The name of the new object.
    :param mesh_name: The name of the contained blender mesh. If None is given, the object name is used.
    :return: The new Mesh object.
    """
    if mesh_name is None:
        mesh_name = object_name
    return create_from_blender_mesh(bpy.data.meshes.new(mesh_name), object_name)

def create_from_point_cloud(points: np.ndarray,
                            object_name: str,
                            add_geometry_nodes_visualization: bool = False,
                            point_size: float = 0.015,
                            point_color: Tuple[float, float, float] = (1, 0, 0)) -> "MeshObject":
    """ Create a mesh from a point cloud.

    The mesh's vertices are filled with the points from the given point cloud.

    :param points: The points of the point cloud. Should be in shape [N, 3]
    :param object_name: The name of the new object.
    :param add_geometry_nodes_visualization: If yes, a geometry nodes modifier is added, 
                                             which adds a sphere to every point. In this way, 
                                             the point cloud will appear in renderings.
    :param point_size: The size of the spheres that are added to the points.
    :param point_color: The color of the spheres that are added to the points.
    :return: The new Mesh object.
    """

    # Create point cloud object and fill it with the given points
    point_cloud = create_with_empty_mesh(object_name)
    point_cloud.get_mesh().from_pydata(points, [], [])
    point_cloud.get_mesh().validate()

    # If desired, add geometry nodes that add a icosphere instance to every point
    if add_geometry_nodes_visualization:
        # Make nodes
        geometry_nodes = point_cloud.add_geometry_nodes()
        mesh_to_points_node = geometry_nodes.nodes.new(type='GeometryNodeMeshToPoints')
        mesh_to_points_node.inputs['Radius'].default_value = point_size

        # Material setup
        material_node = geometry_nodes.nodes.new("GeometryNodeSetMaterial")
        mat = point_cloud.new_material("point_cloud_mat")
        mat.set_principled_shader_value("Base Color", [*point_color, 1])
        material_node.inputs["Material"].default_value = mat.blender_obj

        # Link nodes
        input_node = Utility.get_the_one_node_with_type(geometry_nodes.nodes, "NodeGroupInput")
        output_node = Utility.get_the_one_node_with_type(geometry_nodes.nodes, "NodeGroupOutput")
        geometry_nodes.links.new(input_node.outputs['Geometry'], mesh_to_points_node.inputs['Mesh'])
        geometry_nodes.links.new(mesh_to_points_node.outputs['Points'], material_node.inputs['Geometry'])
        geometry_nodes.links.new(material_node.outputs['Geometry'], output_node.inputs['Geometry'])

    return point_cloud


def create_primitive(shape: str, **kwargs) -> "MeshObject":
    """ Creates a new primitive mesh object.

    :param shape: The name of the primitive to create. Available: ["CUBE", "CYLINDER", "CONE", "PLANE",
                  "SPHERE", "MONKEY"]
    :return: The newly created MeshObject
    """
    if shape == "CUBE":
        bpy.ops.mesh.primitive_cube_add(**kwargs)
    elif shape == "CYLINDER":
        bpy.ops.mesh.primitive_cylinder_add(**kwargs)
    elif shape == "CONE":
        bpy.ops.mesh.primitive_cone_add(**kwargs)
    elif shape == "PLANE":
        bpy.ops.mesh.primitive_plane_add(**kwargs)
    elif shape == "SPHERE":
        bpy.ops.mesh.primitive_uv_sphere_add(**kwargs)
    elif shape == "MONKEY":
        bpy.ops.mesh.primitive_monkey_add(**kwargs)
    else:
        raise Exception("No such shape: " + shape)

    primitive = MeshObject(bpy.context.object)
    # Blender bug: Scale is ignored by default for planes and monkeys.
    # See https://developer.blender.org/T88047
    if 'scale' in kwargs and shape in ["MONKEY", "PLANE"]:
        primitive.set_scale(kwargs['scale'])

    return primitive


def convert_to_meshes(blender_objects: list) -> List[MeshObject]:
    """ Converts the given list of blender objects to mesh objects

    :param blender_objects: List of blender objects.
    :return: The list of meshes.
    """
    return [MeshObject(obj) for obj in blender_objects]


def get_all_mesh_objects() -> List[MeshObject]:
    """
    Returns all mesh objects in scene

    :return: List of all MeshObjects
    """
    return convert_to_meshes(get_all_blender_mesh_objects())


def disable_all_rigid_bodies():
    """ Disables the rigidbody element of all objects """
    for obj in get_all_mesh_objects():
        if obj.has_rigidbody_enabled():
            obj.disable_rigidbody()


def create_bvh_tree_multi_objects(mesh_objects: List[MeshObject]) -> mathutils.bvhtree.BVHTree:
    """ Creates a bvh tree which contains multiple mesh objects.

    Such a tree is later used for fast raycasting.

    :param mesh_objects: The list of mesh objects that should be put into the BVH tree.
    :return: The built BVH tree.
    """
    # Create bmesh which will contain the meshes of all objects
    bm = bmesh.new()
    # Go through all mesh objects
    for obj in mesh_objects:
        # Get a copy of the mesh
        mesh = obj.get_mesh().copy()
        # Apply world matrix 
        mesh.transform(Matrix(obj.get_local2world_mat()))
        # Add object mesh to bmesh
        bm.from_mesh(mesh)
        # Avoid leaving orphan mesh
        bpy.data.meshes.remove(mesh)

    # Create tree from bmesh
    bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
    bm.free()
    return bvh_tree


def compute_poi(objects: List[MeshObject]) -> np.ndarray:
    """ Computes a point of interest in the scene. Point is defined as a location of the one of the selected objects
    that is the closest one to the mean location of the bboxes of the selected objects.

    :param objects: The list of mesh objects that should be considered.
    :return: Point of interest in the scene.
    """
    # Init matrix for all points of all bounding boxes
    mean_bb_points = []

    for obj in objects:
        # Get bounding box corners
        bb_points = obj.get_bound_box()
        # Compute mean coords of bounding box
        mean_bb_points.append(np.mean(bb_points, axis=0))
    # Query point - mean of means
    mean_bb_point = np.mean(mean_bb_points, axis=0)
    # Closest point (from means) to query point (mean of means)
    poi = mean_bb_points[np.argmin(np.linalg.norm(mean_bb_points - mean_bb_point, axis=1))]

    return poi


def scene_ray_cast(origin: Union[Vector, list, np.ndarray], direction: Union[Vector, list, np.ndarray],
                   max_distance: float = 1.70141e+38) -> Tuple[
    bool, np.ndarray, np.ndarray, int, MeshObject, np.ndarray]:
    """ Cast a ray onto all geometry from the scene, in world space.

   :param origin: Origin of the ray, in world space.
   :param direction: Direction of the ray, in world space.
   :param max_distance: Maximum distance.
   :return: Whether the ray successfully hit any geometry
            The hit location of this ray cast, float array of 3 items in [-inf, inf]
            The face normal at the ray cast hit location, float array of 3 items in [-inf, inf]
            The face index, -1 when original data isn’t available, int in [-inf, inf]
            If any object has been hit, the MeshObject otherwise None.
            Some 4x4 matrix.
   """
    hit, location, normal, index, hit_object, matrix = bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),
                                                                                  Vector(origin), Vector(direction),
                                                                                  distance=max_distance)
    if hit_object is not None:
        hit_object = MeshObject(hit_object)
    return hit, np.array(location), np.array(normal), index, hit_object, np.array(matrix)
