from typing import Union, List
import numpy as np
from mathutils import Vector, Euler, Color, Matrix, Quaternion

import bpy

from blenderproc.python.utility.Utility import Utility
from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.BoneUtility import get_constraint, set_ik_constraint, \
    set_ik_limits_from_rotation_constraint


class Inertial(Entity):
    def __init__(self, bpy_object: bpy.types.Object):
        super().__init__(bpy_object=bpy_object)

        object.__setattr__(self, "inertia", None)
        object.__setattr__(self, "mass", None)
        object.__setattr__(self, "origin", None)

    def set_inertia(self, inertia: np.ndarray):
        """ Sets inertia value.

        :param inertia: 3x3 symmetric rotational inertia matrix.
        """
        assert inertia.shape == (3, 3)
        object.__setattr__(self, "inertia", inertia)

    def get_inertia(self) -> np.ndarray:
        """ Returns the inertia.

        :return: The inertia matrix.
        """
        return self.inertia

    def set_mass(self, mass: float):
        """ Sets the mass.

        :param mass: Mass of the link in kilograms.
        """
        object.__setattr__(self, "mass", mass)

    def get_mass(self) -> float:
        """ Returns the mass of the link.

        :return: The mass.
        """
        return self.mass

    def set_origin(self, origin: Union[np.ndarray, Matrix]):
        """ Sets the origin and the world matrix of the inertia.

        :param origin: 4x4 matrix of the inertials relative to the link frame.
        """
        object.__setattr__(self, "origin", Matrix(origin))
        self.blender_obj.matrix_world = Matrix(origin)

    def get_origin(self) -> Matrix:
        """ Returns the origin of the inertia.

        :return: The pose relative to the link frame.
        """
        return self.origin

    def hide(self, hide_object: bool = True):
        """ Sets the visibility of the object.

        :param hide_object: Determines whether the object should be hidden in rendering.
        """
        self.blender_obj.hide_render = hide_object


class Link(Entity):

    def __init__(self, bpy_object: bpy.types.Object):
        super().__init__(bpy_object)

        object.__setattr__(self, 'visuals', [])
        object.__setattr__(self, 'inertial', None)
        object.__setattr__(self, 'collisions', [])
        object.__setattr__(self, 'joint_type', None)
        object.__setattr__(self, 'bone', None)
        object.__setattr__(self, 'fk_bone', None)
        object.__setattr__(self, 'ik_bone', None)
        object.__setattr__(self, 'ik_bone_controller', None)
        object.__setattr__(self, 'ik_bone_constraint', None)
        object.__setattr__(self, 'armature', None)
        object.__setattr__(self, 'child', None)
        object.__setattr__(self, 'fk_ik_mode', "fk")
        object.__setattr__(self, 'link2bone_mat', None)
        object.__setattr__(self, 'visual_local2link_mats', [])
        object.__setattr__(self, 'collision_local2link_mats', [])
        object.__setattr__(self, 'inertial_local2link_mat', None)

    def set_parent(self, parent: "Link"):
        assert isinstance(parent, Link)
        object.__setattr__(self, "parent", parent)

    def get_parent(self) -> "Link":
        return self.parent

    def set_child(self, child: "Link"):
        assert isinstance(child, Link)
        object.__setattr__(self, "child", child)

    def get_child(self) -> "Link":
        return self.child

    def _set_rotation_euler(self, bone: bpy.types.PoseBone,
                            rotation_euler: Union[float, List[float], Euler, np.ndarray], mode: str = "absolute"):
        """ Rotates the bone based on euler angles. Validates values with given constraints.

        :param bone: The bone to be rotated.
        :param rotation_euler: The amount of rotation (in radians). Either three floats for x, y and z axes, or a
                               single float. In the latter case, the axis of rotation is derived based on the rotation
                               constraint. If these are not properly set (i.e., two axes must have equal min/max
                               values) an exception will be thrown.
        :param mode: One of ["absolute", "relative"]. For absolute rotations we clip the rotation value based on the
                     constraints. For relative we don't - this will result in inverse motion after the constraint's
                     limits have been reached.
        """
        assert mode in ["absolute", "relative"]

        bpy.ops.object.select_all(action='DESELECT')

        bone.bone.select = True
        bone.rotation_mode = 'XYZ'

        # in absolute mode we overwrite the rotation values of the armature
        if mode == "absolute":
            if isinstance(rotation_euler, float):
                axis = self._determine_rotation_axis(bone=bone)
                rotation_euler = self._clip_value_from_constraint(bone=bone, value=rotation_euler,
                                                                  constraint_name="Limit Rotation", axis=axis)
                current_rotation_euler = bone.rotation_euler
                current_rotation_euler[["X", "Y", "Z"].index(axis)] = rotation_euler
                bone.rotation_euler = current_rotation_euler
                print(f"Set rotation_euler of bone {bone.name} to {rotation_euler}")
            else:
                bone.rotation_euler = Vector(
                    [self._clip_value_from_constraint(bone=bone, value=rot_euler, constraint_name="Limit Rotation",
                                                      axis=axis)
                     for rot_euler, axis in zip(rotation_euler, ["X", "Y", "Z"])])
                print(f"Set rotation_euler of bone {bone.name} to {rotation_euler}")
        # in relative mode we add the rotation to the current value
        elif mode == "relative":
            if isinstance(rotation_euler, float):
                axis = self._determine_rotation_axis(bone=bone)
                if axis is not None:
                    bone.rotation_euler.rotate_axis(axis, rotation_euler)
                else:
                    for axis in ['X', 'Y', 'Z']:
                        bone.rotation_euler.rotate_axis(axis, rotation_euler)
                print(f"Relatively rotated bone {bone.name} around axis {axis} for {rotation_euler} radians")
            else:
                for axis, rotation in zip(["X", "Y", "Z"], rotation_euler):
                    bone.rotation_euler.rotate_axis(axis, rotation)
                print(f"Relatively rotated {bone.name} for {rotation_euler} radians")

    def set_rotation_euler(self, *args, **kwargs):
        raise NotImplementedError("Please use 'set_rotation_euler_fk()' or set_rotation_euler_ik()'!")

    def set_location(self, *args, **kwargs):
        raise NotImplementedError("Please use 'set_location_ik()'!")

    def set_rotation_euler_fk(self, *args, **kwargs):
        if self.get_fk_ik_mode() != "fk":
            self.switch_fk_ik_mode(mode="fk")
        self._set_rotation_euler(bone=self.fk_bone, *args, **kwargs)

    def set_rotation_euler_ik(self, *args, **kwargs):
        if self.get_fk_ik_mode() != "ik":
            self.switch_fk_ik_mode(mode="ik")
        self._set_rotation_euler(bone=self.ik_bone_controller, *args, **kwargs)

    def set_location_ik(self, location: Union[List[float], np.array, Vector]):
        """ Sets the location of the ik bone controller in inverse kinematics mode.

        :param location: Location vector.
        """
        if self.get_fk_ik_mode() != "ik":
            self.switch_fk_ik_mode(mode="ik")

        if not isinstance(location, Vector):
            location = Vector(location)
        assert self.ik_bone_controller is not None, f"No ik bone chain created. Please run " \
                                                    f"'urdf_object.create_ik_bone_controller()' first!"

        # first: determine offset to base frame
        self.ik_bone_controller.location = Vector([0., 0., 0.])
        self.ik_bone_controller.rotation_mode = "XYZ"
        self.ik_bone_controller.rotation_euler = Vector([0., 0., 0.])
        bpy.context.view_layer.update()
        offset_mat = self.ik_bone_controller.matrix

        # offset location by ik offset to base bones
        location = location + (self.ik_bone.head - self.bone.head)
        location = Vector([location[0], location[1], location[2], 1.])

        # move to current frame
        location = offset_mat.inverted() @ location
        self.ik_bone_controller.location = location[:3]

    def _determine_rotation_axis(self, bone: bpy.types.PoseBone) -> Union[str, None]:
        """ Determines the single rotation axis and checks if the constraints are set well to have only one axis of
            freedom.

        :param bone: Bone of which the rotation axis will be determined.
        :return: The single rotation axis ('X', 'Y' or 'Z') or None if no constraint is set..
        """
        c = get_constraint(bone=bone, constraint_name="Limit Rotation")
        if c is None:
            print("WARNING: No rotation constraint set. Will rotate all axes relatively!")
            return None

        axes = ['X', 'Y', 'Z']
        if c.use_limit_x and c.min_x == c.max_x:
            axes.pop(axes.index('X'))
        if c.use_limit_y and c.min_y == c.max_y:
            axes.pop(axes.index('Y'))
        if c.use_limit_z and c.min_z == c.max_z:
            axes.pop(axes.index('Z'))
        assert len(axes) == 1, f"Constraints are set wrong for a rotation around a single axis. Only one axis should " \
                               f"be allowed to move, but found freedom in {len(axes)} axes of armature " \
                               f"{self.get_name()} (constraint: {c}, uses limits (xyz): " \
                               f"{c.use_limit_x, c.use_limit_y, c.use_limit_z}, " \
                               f"values: {c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z})."

        return axes[0]

    def _clip_value_from_constraint(self, bone: bpy.types.PoseBone, value: float = 0, constraint_name: str = "",
                                    axis: str = "X") -> float:
        """ Checks if an axis is constraint, and clips the value to the min/max of this constraint. If the constraint
            does not exist, nothing is done.

        :param bone: The bone from which the constraints will be determined.
        :param value: Value to be clipped.
        :param constraint_name: Name of the constraint.
        :param axis: Axis to check.
        :return: Clipped value if a constraint is set, else the initial value.
        """
        c = get_constraint(bone=bone, constraint_name=constraint_name)
        if c is not None:
            min_value = eval(f"c.min_{axis.lower()}")
            max_value = eval(f"c.max_{axis.lower()}")
            print(f"Clipping {value} to be in range {min_value}, {max_value}")
            if value < min_value:
                return min_value
            elif value > max_value:
                return max_value
        return value

    def set_visuals(self, visuals: List[MeshObject]):
        object.__setattr__(self, "visuals", visuals)

    def get_visuals(self) -> List[MeshObject]:
        return self.visuals

    def set_collisions(self, collisions: List[MeshObject]):
        object.__setattr__(self, "collisions", collisions)

    def get_collisions(self) -> List[MeshObject]:
        return self.collisions

    def set_inertial(self, inertial: Inertial):
        object.__setattr__(self, "inertial", inertial)

    def get_inertial(self) -> Inertial:
        return self.inertial

    def set_bone(self, bone: bpy.types.PoseBone):
        """ Sets the bone controlling the visuals / collisions / inertial of the link.

        :param bone: The bone.
        """
        object.__setattr__(self, "bone", bone)

    def set_fk_bone(self, bone: bpy.types.PoseBone):
        """ Sets the bone controlling the forward kinematic motion of this link.

        :param bone: The bone.
        """
        object.__setattr__(self, "fk_bone", bone)

    def set_ik_bone(self, bone: bpy.types.PoseBone):
        """ Sets the bone controlling the inverse kinematic motion of this link.

        :param bone: The bone.
        """
        object.__setattr__(self, "ik_bone", bone)

    def set_ik_bone_controller(self, bone: bpy.types.PoseBone):
        """ Sets the control bone controlling the inverse kinematic motion for this link.

        :param bone: The bone.
        """
        object.__setattr__(self, "ik_bone_controller", bone)

    def set_ik_bone_constraint(self, bone: bpy.types.PoseBone):
        """ Sets the constraint bone responsible for constraining to inverse kinematic motion.

        :param bone: The bone.
        """
        object.__setattr__(self, "ik_bone_constraint", bone)

    def set_armature(self, armature: bpy.types.Armature):
        """ Sets the armature which holds all the bones of all links.

        :param armature: The armature.
        """
        object.__setattr__(self, "armature", armature)

    def _set_fk_ik_mode(self, mode="fk"):
        """ Sets the mode of the link.

        :param mode: One of ["fk", "ik"] denoting forward or inverse kinematics mode.
        """
        object.__setattr__(self, "fk_ik_mode", mode)

    def set_link2bone_mat(self, matrix: Matrix):
        """ Sets the transformation matrix from bone to link.

        :param matrix: The transformation from bone to link.
        """
        object.__setattr__(self, "link2bone_mat", matrix)

    def set_visual_local2link_mats(self, matrix_list: List[Matrix]):
        """ Sets the transformation matrices from link to the visual parts.

        :param matrix_list: List of transformation matrices.
        """
        object.__setattr__(self, "visual_local2link_mats", matrix_list)

    def set_collision_local2link_mats(self, matrix_list: List[Matrix]):
        """ Sets the transformation matrices from link to the collision parts.

        :param matrix_list: List of transformation matrices.
        """
        object.__setattr__(self, "collision_local2link_mats", matrix_list)

    def set_inertial_local2link_mat(self, matrix: Matrix):
        """ Sets the transformation matrix from link to inertial.

        :param matrix: The transformation matrix from link to inertial.
        """
        object.__setattr__(self, "inertial_local2link_mat", matrix)

    def hide(self, hide_object: bool = True):
        """ Sets the visibility of the object and all visual, collision and inertial parts.

        :param hide_object: Determines whether the object should be hidden in rendering.
        """
        self.hide(hide_object=hide_object)
        for obj in self.get_all_objs():
            obj.hide(hide_object=hide_object)

    def get_visual_local2world_mats(self) -> Union[List, None]:
        """Returns the transformation matrices from world to the visual parts.

        :return: List of transformation matrices.
        """
        bpy.context.view_layer.update()
        bone_mat = Matrix.Identity(4)
        if self.bone is not None:
            bone_mat = self.bone.matrix
        if self.visuals != []:
            return [bone_mat @ (self.link2bone_mat.inverted() @ visual_local2link_mat) for visual_local2link_mat in
                    self.visual_local2link_mats]
        else:
            return None

    def get_collision_local2world_mats(self) -> Union[List, None]:
        """Returns the transformation matrices from world to the collision parts.

        :return: List of transformation matrices.
        """
        bpy.context.view_layer.update()
        bone_mat = Matrix.Identity(4)
        if self.bone is not None:
            bone_mat = self.bone.matrix
        if self.collisions != []:
            return [bone_mat @ (self.link2bone_mat.inverted() @ collision_local2link_mat) for collision_local2link_mat
                    in self.collision_local2link_mats]
        else:
            return None

    def get_inertial_local2world_mat(self) -> Matrix:
        """Returns the transformation matrix from world to the inertial part.

        :return: The transformation matrix.
        """
        bpy.context.view_layer.update()
        bone_mat = Matrix.Identity(4)
        if self.bone is not None:
            bone_mat = self.bone.matrix
        if self.inertial is not None:
            return bone_mat @ (self.link2bone_mat.inverted() @ self.inertial_local2link_mat)
        else:
            return None

    def get_all_objs(self):
        return self.visuals + self.collisions + ([self.inertial] if self.inertial is not None else [])

    def set_joint_type(self, joint_type: Union[str, None]):
        """ Sets the joint type of the link which specifies the connection to its parent.

        :param joint_type: One of ['fixed', 'prismatic', 'revolute', 'continuous', 'planar', 'floating' or None].
        """
        object.__setattr__(self, "joint_type", joint_type)

    def get_joint_type(self) -> Union[str, None]:
        """ Returns the joint type.

        :return: The joint type of the armature.
        """
        return self.joint_type

    def parent_with_bone(self, weight_distribution='rigid'):
        """ Parents all objects of the link to the bone.

        :param weight_distribution: One of ['envelope', 'automatic', 'rigid']. For more information please see
                                    https://docs.blender.org/manual/en/latest/animation/armatures/skinning/parenting.html.
        """
        assert weight_distribution in ['envelope', 'automatic', 'rigid']

        if self.bone is None:
            # only set parent
            print(f"WARNING: Link {self.get_name()} does not have a bone to be parented with (usually because it's the "
                  f"first link)!")
            self.blender_obj.parent = self.armature
            return

        if weight_distribution in ['envelope', 'automatic']:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
            self.select()
            for obj in self.get_all_objs():
                obj.select()
            self.armature.select_set(True)
            bpy.context.view_layer.objects.active = self.armature
            bpy.ops.object.mode_set(mode='POSE')
            if weight_distribution == 'envelope':
                bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')
            else:
                bpy.ops.object.parent_set(type='ARMATURE_AUTO')
            bpy.ops.object.mode_set(mode='OBJECT')
        elif weight_distribution == 'rigid':
            for obj in self.get_all_objs() + [self]:
                bpy.ops.object.select_all(action='DESELECT')
                obj.blender_obj.parent = self.armature
                bpy.context.view_layer.objects.active = obj.blender_obj
                mod = obj.blender_obj.modifiers.new("Armature", "ARMATURE")
                mod.object = self.armature
                obj.blender_obj.vertex_groups.new(name=self.bone.name)
                vertices = [v.index for v in obj.blender_obj.data.vertices]
                obj.blender_obj.vertex_groups[0].add(vertices, 1.0, 'REPLACE')
        bpy.ops.object.select_all(action='DESELECT')

    def _create_ik_bone_controller(self, relative_location: Union[List[float], Vector] = [0., 0., 0.],
                                   use_rotation=True,
                                   chain_length=0) -> (bpy.types.PoseBone, bpy.types.PoseBone, Matrix):
        """ Creates an ik bone controller and a corresponding constraint bone for the respective link.

        :param relative_location: Relative location of the ik bone controller w.r.t. the bone's location. This can be
                                  used to shift the point of control further away from the end effector.
        :param use_rotation: Whether to rotate the child links as well. Defaults to True.
        :param chain_length: The number of parent links which are influenced by this ik bone. Defaults to 0 for all
                             parents.
        :return: Constraint and control bone.
        """
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode='EDIT')
        self.armature.select_set(True)
        edit_bones = self.armature.data.edit_bones

        # we need two bones: a controll bone and a constraint bone
        # the controll bone will be placed exactly where the current ik bone is
        ik_bone_controller = edit_bones.new(self.ik_bone.name + '.controller')
        ik_bone_controller.head = self.ik_bone.head + Vector(relative_location)
        ik_bone_controller.tail = self.ik_bone.tail + Vector(relative_location)
        ik_bone_controller.parent = edit_bones[self.bone.name].parent_recursive[-1]

        # the constraint bone will be placed at the head of the ik bone
        ik_bone_constraint = edit_bones.new(self.ik_bone.name + '.constraint')
        ik_bone_constraint.tail = self.ik_bone.head + Vector(relative_location)
        ik_bone_constraint.head = ik_bone_constraint.tail - (self.ik_bone.tail - self.ik_bone.head)
        # we need to re-parent the pre- and successor of the constraint bone
        ik_bone_constraint.parent = edit_bones[self.ik_bone.name].parent_recursive[0]
        edit_bones[self.ik_bone.name].parent = edit_bones[ik_bone_constraint.name]

        # add the bones to the link
        bpy.ops.object.mode_set(mode='POSE')
        self.set_ik_bone_constraint(self.armature.pose.bones.get(self.ik_bone.name + '.constraint'))
        self.set_ik_bone_controller(self.armature.pose.bones.get(self.ik_bone.name + '.controller'))

        # add ik constraint
        set_ik_constraint(self.ik_bone_constraint, self.armature, self.ik_bone_controller.name,
                          use_rotation=use_rotation, chain_length=chain_length)

        if self.get_joint_type() == "revolute":
            set_ik_limits_from_rotation_constraint(self.ik_bone_constraint,
                                                   constraint=self.bone.constraints["Limit Rotation"])

        bpy.ops.object.mode_set(mode='OBJECT')

        # determine offset
        bpy.context.view_layer.update()
        offset = self.ik_bone_constraint.matrix.inverted() @ self.ik_bone_controller.matrix

        return self.ik_bone_constraint, self.ik_bone_controller, offset

    def get_fk_ik_mode(self) -> str:
        return self.fk_ik_mode

    def switch_fk_ik_mode(self, mode="fk", keep_pose=True):
        """ Switches between forward and inverse kinematics mode. Will do this automatically when switching between e.g.
            `set_rotation_euler_fk()` and `set_rotation_euler_ik()`.

        :param mode: One of "fk", "ik".
        :param keep_pose: If specified, will keep the pose when switching modes. Otherwise will return to the old pose
                          of the previously selected mode.
        """
        if self.bone is None:
            return
        assert mode in ["fk", "ik"]
        if mode == "fk":  # turn off copy rotation constraints of fk bone and base bone
            if self.get_fk_ik_mode() == "fk":
                return True
            bpy.context.view_layer.update()

            if keep_pose:
                self.fk_bone.matrix = self.ik_bone.matrix
            if self.joint_type == "revolute":
                self.bone.constraints["copy_rotation.fk"].influence = 1.
                self.bone.constraints["copy_rotation.ik"].influence = 0.

            if "copy_rotation.ik" in self.bone.constraints.keys():
                self.bone.constraints["copy_rotation.ik"].influence = 0.  # otherwise skip

            if self.ik_bone_controller is not None:  # switch off ik constraint
                self.ik_bone_constraint.constraints["IK"].influence = 0.
            self._set_fk_ik_mode(mode="fk")

        else:  # turn off copy rotation constraints of ik bone and base bone
            if self.get_fk_ik_mode() == "ik":
                return True
            bpy.context.view_layer.update()

            if keep_pose:
                self.ik_bone.matrix = self.fk_bone.matrix

            if self.joint_type == "revolute":
                self.bone.constraints["copy_rotation.fk"].influence = 0.
                self.bone.constraints["copy_rotation.ik"].influence = 1.

            self._set_fk_ik_mode(mode="ik")
            if self.ik_bone_controller is not None:
                bpy.context.view_layer.update()
                location = np.array(self.armature.pose.bones[self.bone.name].head)  # or matrix?
                print("desired ik location", location)
                # location = Vector(np.array(mat)[:3, -1])
                self.set_location_ik(location)

            if self.ik_bone_constraint is not None:
                self.ik_bone_constraint.constraints["IK"].influence = 1.
                fk_bone_mat = np.array(self.fk_bone.matrix)
                fk_bone_mat[:3, -1] = np.array(self.ik_bone_controller.matrix)[:3, -1]
                self.ik_bone_controller.matrix = Matrix(fk_bone_mat)


class URDFObject(Entity):

    def __init__(self, armature: bpy.types.Armature, links: List[Link], xml_tree: Union["urdfpy.URDF", None] = None):
        super().__init__(bpy_object=armature)

        object.__setattr__(self, "links", links)
        object.__setattr__(self, "xml_tree", xml_tree)
        object.__setattr__(self, "ik_bone_constraint", None)
        object.__setattr__(self, "ik_bone_controller", None)
        object.__setattr__(self, "fk_ik_mode", None)
        object.__setattr__(self, "ik_link", None)
        object.__setattr__(self, 'ik_bone_offset', None)

    def get_all_urdf_objs(self) -> List[Union[Link, Inertial, MeshObject]]:
        """ Returns a list of all urdf-related objects.

        :return: List of all urdf-related objects.
        """
        objs = []
        for link in self.links:
            objs.append(link)
            objs.extend(link.get_all_objs())
        return objs

    def get_all_collision_objs(self) -> List[MeshObject]:
        """ Returns a list of all collision objects.

        :return: List of all collision objects.
        """
        return [obj for obj in self.get_all_urdf_objs() if 'collision' in obj.get_name()]

    def get_all_inertial_objs(self) -> List[Inertial]:
        """ Returns a list of all inertial objects.

        :return: List of all inertial objects.
        """
        return [obj for obj in self.get_all_urdf_objs() if isinstance(obj, Inertial)]

    def get_all_visual_objs(self) -> List[MeshObject]:
        """ Returns a list of all visual objects.

        :return: List of all visual objects.
        """
        return [obj for obj in self.get_all_urdf_objs() if 'visual' in obj.get_name()]

    def hide_irrelevant_objs(self):
        """ Hides links and their respective collision and inertial objects from rendering. """
        self.blender_obj.hide_set(True)
        for link in self.links:
            for obj in link.get_all_objs():
                if "collision" in obj.get_name() or "inertial" in obj.get_name():
                    obj.hide()

    def set_ascending_category_ids(self, category_ids: Union[List[int], None] = None):
        """ Sets semantic categories to the links and their associated objects.

        :param category_ids: List of 'category_id's for every link. If None, will create a list from [1 ... len(links)].
        """
        if category_ids is None:
            category_ids = list(range(1, len(self.links) + 1))

        assert len(category_ids) == len(self.links), f"Need equal amount of category ids for links. Got " \
                                                     f"{len(category_ids)} and {len(self.links)}, respectively."
        for link, category_id in zip(self.links, category_ids):
            link.set_cp(key="category_id", value=category_id)
            for obj in link.get_all_objs():
                obj.set_cp(key="category_id", value=category_id)

    def remove_link_by_index(self, index: int = 0):
        """ Removes a link and all its associated objects given an index. Also handles relationship of the link's child
            with its parent. This is useful for removing a 'world link' which could be a simple flat surface, or if
            someone wants to shorten the whole urdf object.

        :param index: Index of the joint to be removed.
        """
        assert index < len(self.links), f"Invalid index {index}. Index must be in range 0, {len(self.links)} (no. " \
                                        f"links: {len(self.links)})."

        # remove link from the urdf instance and determine child / parent
        link_to_be_removed = self.links.pop(index)
        child = link_to_be_removed.get_child()

        # remove bones and assign old bone pose to child bone
        if child is not None and link_to_be_removed.bone is not None:
            print(f'Trying to put {child.get_name()} to position of {link_to_be_removed.get_name()}')
            bpy.context.view_layer.update()
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = self.blender_obj
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            edit_bones = self.blender_obj.data.edit_bones
            offset = edit_bones[child.bone.name].head - edit_bones[link_to_be_removed.bone.name].head

            edit_bones[child.bone.name].head -= offset
            edit_bones[child.bone.name].tail -= offset
            edit_bones[child.fk_bone.name].head -= offset
            edit_bones[child.fk_bone.name].tail -= offset
            edit_bones[child.ik_bone.name].head -= offset
            edit_bones[child.ik_bone.name].tail -= offset

            grand_child = child.get_child()
            while grand_child is not None:
                edit_bones[grand_child.bone.name].head -= offset
                edit_bones[grand_child.bone.name].tail -= offset
                edit_bones[grand_child.fk_bone.name].head -= offset
                edit_bones[grand_child.fk_bone.name].tail -= offset
                edit_bones[grand_child.ik_bone.name].head -= offset
                edit_bones[grand_child.ik_bone.name].tail -= offset
                grand_child = grand_child.get_child()

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.update()

            # do the same for the link objects
            for obj in child.get_all_objs():
                obj.set_location(location=obj.get_location() - offset)
            grand_child = child.get_child()
            while grand_child is not None:
                for obj in grand_child.get_all_objs():
                    obj.set_location(location=obj.get_location() - offset)
                grand_child = grand_child.get_child()

            if link_to_be_removed == self.ik_link:
                self._set_ik_link(None)

            for obj in link_to_be_removed.get_all_objs():
                obj.delete()
            link_to_be_removed.delete()

    def hide(self, hide_object: bool = True):
        """ Sets the visibility of the object.

        :param hide_object: Determines whether the object should be hidden in rendering.
        """
        self.hide()
        for link in self.links:
            link.hide(hide_object=hide_object)

    def get_all_local2world_mats(self) -> np.array:
        """ Returns all matrix_world matrices from every joint. """

        bpy.context.view_layer.update()
        matrices = []
        for link in self.links:
            if link.bone is not None:
                matrices.append(link.bone.matrix)
        return np.stack(matrices)

    def get_all_visual_local2world_mats(self) -> np.array:
        """ Returns all transformations from world frame to the visual objects. """
        return np.stack([link.get_visual_local2world_mats() for link in self.links])

    def get_all_collision_local2world_mats(self) -> np.array:
        """ Returns all transformations from the world frame to the collision objects. """
        return np.stack([link.get_collision_local2world_mats() for link in self.links])

    def get_all_inertial_local2world_mats(self) -> np.array:
        """ Returns all transformations from the world frame to the inertial objects. """
        return np.stack([link.get_inertial_local2world_mat() for link in self.links])

    def _set_ik_bone_controller(self, bone: bpy.types.PoseBone):
        object.__setattr__(self, "ik_bone_controller", bone)

    def _set_ik_bone_constraint(self, bone: bpy.types.PoseBone):
        object.__setattr__(self, "ik_bone_constraint", bone)

    def _set_fk_ik_mode(self, mode: str = "fk"):
        object.__setattr__(self, "fk_ik_mode", mode)

    def _set_ik_link(self, ik_link: Union[Link, None]):
        object.__setattr__(self, "ik_link", ik_link)

    def create_ik_bone_controller(self, link: Union[Link, None] = None,
                                  relative_location: Union[List[float], Vector] = [0., 0., 0.], use_rotation: bool = True,
                                  chain_length: int = 0):
        """ Creates an ik bone controller and a corresponding constraint bone for the respective link.

        :param link: The link to create an ik bone for. If None, will use the last link.
        :param relative_location: Relative location of the ik bone controller w.r.t. the bone's location. This can be
                                  used to shift the point of control further away from the end effector.
        :param use_rotation: Whether to rotate the child links as well. Defaults to True.
        :param chain_length: The number of parent links which are influenced by this ik bone. Defaults to 0 for all
                             parents.
        """
        if self.ik_bone_controller is not None:
            raise NotImplementedError("URDFObject already has an ik bone controller. More than one ik controllers are "
                                      "currently not supported!")
        if link is None:
            link = self.links[-1]
        ik_bone_controller, ik_bone_constraint, offset = link._create_ik_bone_controller(
            relative_location=relative_location, use_rotation=use_rotation, chain_length=chain_length)
        self._set_ik_bone_controller(ik_bone_controller)
        self._set_ik_bone_constraint(ik_bone_constraint)
        self._set_ik_bone_offset(offset=offset)
        self._set_ik_link(link)
        self._switch_fk_ik_mode(mode="ik")

    def _switch_fk_ik_mode(self, mode: str = "fk", keep_pose: bool = True):
        """ Switches between forward and inverse kinematics mode. Will do this automatically when switching between e.g.
            `set_rotation_euler_fk()` and `set_rotation_euler_ik()`.

        :param mode: One of "fk", "ik".
        :param keep_pose: If specified, will keep the pose when switching modes. Otherwise will return to the old pose
                          of the previously selected mode.
        """
        if mode == "ik" and self.ik_bone_controller is None:
            raise NotImplementedError("URDFObject doesn't have an ik bone controller. Please set up an ik bone first "
                                      "with 'urdf_object.create_ik_bone_controller()'")
        if self.fk_ik_mode != mode:
            for link in self.links:
                link.switch_fk_ik_mode(mode=mode, keep_pose=keep_pose)
            self._set_fk_ik_mode(mode=mode)

    def get_revolute_joints(self) -> List[Link]:
        return [link for link in self.links if link.joint_type == "revolute"]

    def _set_keyframe(self, name: str, frame: int = 0):
        """ Sets a keyframe for a specific name for all bones of all links, as well as the copy_rotation constraint for
            revolute joints.

        :param name: Name of the keyframe to be inserted.
        :param frame: Where to insert the keyframe.
        """
        bpy.context.view_layer.update()
        Utility.insert_keyframe(self.blender_obj, name, frame)
        for link in self.links:
            if link.bone is not None:
                Utility.insert_keyframe(link.bone, name, frame)
                Utility.insert_keyframe(link.fk_bone, name, frame)
                Utility.insert_keyframe(link.ik_bone, name, frame)
                if link.joint_type == 'revolute':
                    Utility.insert_keyframe(link.bone.constraints['copy_rotation.fk'], "influence", frame=frame)
                    Utility.insert_keyframe(link.bone.constraints['copy_rotation.ik'], "influence", frame=frame)
        if self.ik_bone_controller is not None:
            Utility.insert_keyframe(self.ik_bone_controller, name, frame)
        if self.ik_bone_constraint is not None:
            Utility.insert_keyframe(self.ik_bone_constraint, name, frame)

        if frame > bpy.context.scene.frame_end:
            bpy.context.scene.frame_end += 1

    def set_rotation_euler_fk(self, link: Union[Link, None], rotation_euler: Union[float, List[float], Euler, np.ndarray],
                              mode: str = "absolute", frame: int = 0):
        """ Rotates one specific link or all links based on euler angles in forward kinematic mode. Validates values
            with given constraints.

        :param link: The link to be rotated. If None, will perform the rotation on all revolute joints.
        :param rotation_euler: The amount of rotation (in radians). Either three floats for x, y and z axes, or a
                               single float. In the latter case, the axis of rotation is derived based on the rotation
                               constraint. If these are not properly set (i.e., two axes must have equal min/max
                               values) an exception will be thrown.
        :param mode: One of ["absolute", "relative"]. For absolute rotations we clip the rotation value based on the
                     constraints. For relative we don't - this will result in inverse motion after the constraint's
                     limits have been reached.
        :param frame: The keyframe where to insert the rotation.
        """
        self._switch_fk_ik_mode(mode="fk")
        if link is not None:
            link.set_rotation_euler_fk(rotation_euler=rotation_euler, mode=mode)
        else:
            revolute_joints = self.get_revolute_joints()
            if isinstance(rotation_euler, list) and len(revolute_joints) == len(rotation_euler):
                for revolute_joint, rotation in zip(revolute_joints, rotation_euler):
                    revolute_joint.set_rotation_euler_fk(rotation_euler=rotation, mode=mode)
            else:
                for revolute_joint in revolute_joints:
                    revolute_joint.set_rotation_euler_fk(rotation_euler=rotation_euler, mode=mode)
        self._set_keyframe(name="rotation_euler", frame=frame)

    def set_rotation_euler_ik(self, rotation_euler: Union[float, List[float], Euler, np.ndarray],
                              mode: str = "absolute", frame: int = 0):
        """ Performs rotation in inverse kinematics mode.

        :param rotation_euler: The amount of rotation (in radians). Either three floats for x, y and z axes, or a
                               single float. In the latter case, the axis of rotation is derived based on the rotation
                               constraint. If these are not properly set (i.e., two axes must have equal min/max
                               values) an exception will be thrown.
        :param mode: One of ["absolute", "relative"]. For absolute rotations we clip the rotation value based on the
                     constraints. For relative we don't - this will result in inverse motion after the constraint's
                     limits have been reached.
        :param frame: The keyframe where to insert the rotation.
        """
        self._switch_fk_ik_mode(mode="ik")
        assert self.ik_link is not None
        self.ik_link.set_rotation_euler_ik(rotation_euler=rotation_euler, mode=mode)
        self._set_keyframe(name="rotation_euler", frame=frame)

    def set_location_ik(self, location: Union[List[float], np.array, Vector], frame: int = 0):
        """ Performs location change in inverse kinematics mode.

        :param location: Location vector.
        :param frame: The keyframe where to insert the rotation.
        """
        self._switch_fk_ik_mode(mode="ik")
        assert self.ik_link is not None
        self.ik_link.set_location_ik(location=location)
        self._set_keyframe(name="location", frame=frame)

    def has_reached_ik_pose(self, location_error: float = 0.01, rotation_error: float = 0.01) -> bool:
        """ Checks whether the urdf object was able to move to the currently set pose.

        :param location_error: Tolerable location error in m.
        :param rotation_error: Tolerable rotation error in radians.
        :return: True if the link is at the desired ik pose; else False.
        """
        curr_offset = self.ik_bone_controller.matrix.inverted() @ self.ik_bone_constraint.matrix
        t_curr, q_curr, _ = curr_offset.decompose()
        t_orig, q_orig, _ = self.ik_bone_offset.decompose()

        t_diff = (t_curr - t_orig).length
        q_diff = q_curr.rotation_difference(q_orig).angle

        if t_diff < location_error and q_diff < rotation_error:
            print(f'Pose is within in given constraints:\n'
                  f'  translation difference: {t_diff:.4f} (max: {location_error})\n'
                  f'  rotation difference: {q_diff:.4f} (max: {rotation_error})')
            return True
        else:
            print(f'Pose is not within given constraints:\n'
                  f'  translation difference: {t_diff:.4f} (max: {location_error})\n'
                  f'  rotation difference: {q_diff:.4f} (max: {rotation_error})')
            return False

    def _set_ik_bone_offset(self, offset: Matrix):
        """ Sets the location offset between the control and constraint bone.

        :param offset: The location offset.
        """
        object.__setattr__(self, "ik_bone_offset", offset)
