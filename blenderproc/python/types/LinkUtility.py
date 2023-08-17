""" All link objects are captured in this class. """

from typing import Union, List, Optional, Tuple

import bpy
import numpy as np
from mathutils import Vector, Euler, Matrix
from trimesh import Trimesh

from blenderproc.python.utility.Utility import KeyFrame
from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.BoneUtility import get_constraint, set_ik_constraint, \
    set_ik_limits_from_rotation_constraint
from blenderproc.python.types.InertialUtility import Inertial


# as all attributes are accessed via the __getattr__ and __setattr__ in this module, we need to remove the member
# init check
# pylint: disable=no-member
class Link(Entity):
    """
    Every instance of this class is a link which is usually part of an URDFObject. It can have objects attached to it,
    and different types of armature bones for manipulation.
    """
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

    def set_link_parent(self, parent: "Link"):
        """ Sets the parent of this link.

        :param parent: Parent link.
        """
        assert isinstance(parent, Link)
        object.__setattr__(self, "parent", parent)

    def get_link_parent(self) -> "Link":
        """ Returns this link's parent.

        :return: Parent link.
        """
        return self.parent

    def set_link_child(self, child: "Link"):
        """ Sets the child of this link.

        :param child: Child link.
        """
        assert isinstance(child, Link)
        object.__setattr__(self, "child", child)

    def get_link_child(self) -> "Link":
        """ Returns this link's child.

        :return: Child link.
        """
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
        """ Sets the rotation for this link in forward kinematics mode. See self._set_rotation_euler() for details. """
        if self.get_fk_ik_mode() != "fk":
            self.switch_fk_ik_mode(mode="fk")
        self._set_rotation_euler(bone=self.fk_bone, *args, **kwargs)

    def set_rotation_euler_ik(self, *args, **kwargs):
        """ Sets the rotation for this link in inverse kinematics mode. See self._set_rotation_euler() for details. """
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
        assert self.ik_bone_controller is not None, "No ik bone chain created. Please run " \
                                                    "'urdf_object.create_ik_bone_controller()' first!"

        # first: determine offset to base frame
        self.ik_bone_controller.location = Vector([0., 0., 0.])
        self.ik_bone_controller.rotation_mode = "XYZ"
        self.ik_bone_controller.rotation_euler = Vector([0., 0., 0.])
        bpy.context.view_layer.update()
        offset_mat = self.ik_bone_controller.matrix

        # offset location by ik offset to base bones
        location += (self.ik_bone.head - self.bone.head)
        location = Vector([location[0], location[1], location[2], 1.])

        # move to current frame
        location = offset_mat.inverted() @ location
        self.ik_bone_controller.location = location[:3]

    def _determine_rotation_axis(self, bone: bpy.types.PoseBone) -> Optional[str]:
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
            min_value = {"x": c.min_x, "y": c.min_y, "z": c.min_z}[axis.lower()]
            max_value = {"x": c.max_x, "y": c.max_y, "z": c.max_z}[axis.lower()]
            print(f"Clipping {value} to be in range {min_value}, {max_value}")
            if value < min_value:
                return min_value
            if value > max_value:
                return max_value
        return value

    def set_visuals(self, visuals: List[MeshObject]):
        """ Sets the visual meshes for this link.

        :param visuals: List of visual meshes.
        """
        object.__setattr__(self, "visuals", visuals)

    def get_visuals(self) -> List[MeshObject]:
        """ Returns the visual meshes for this link.

        :return: List of visual meshes.
        """
        return self.visuals

    def set_collisions(self, collisions: List[MeshObject]):
        """ Sets the collision meshes for this link.

        :param collisions: List of collision meshes.
        """
        object.__setattr__(self, "collisions", collisions)

    def get_collisions(self) -> List[MeshObject]:
        """ Returns the collision meshes for this link.

        :return: List of collision meshes.
        """
        return self.collisions

    def set_inertial(self, inertial: Inertial):
        """ Sets the inertial meshes for this link.

        :param inertial: List of inertial meshes.
        """
        object.__setattr__(self, "inertial", inertial)

    def get_inertial(self) -> Inertial:
        """ Returns the inertial meshes for this link.

        :return: List of inertial meshes.
        """
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

    def get_visual_local2world_mats(self, parent2world_matrix: Optional[Matrix] = None) -> Optional[List[Matrix]]:
        """Returns the transformation matrices from world to the visual parts.

        :param parent2world_matrix: The transformation from the link's armature to the world frame.
        :return: List of transformation matrices.
        """
        bpy.context.view_layer.update()
        if parent2world_matrix is None:
            parent2world_matrix = Matrix(Entity(self.armature).get_local2world_mat())
        bone_mat = Matrix.Identity(4)
        if self.bone is not None:
            bone_mat = self.bone.matrix
        if self.visuals:
            link2base_mats = [bone_mat @ (self.link2bone_mat.inverted() @ visual_local2link_mat) for
                              visual_local2link_mat in self.visual_local2link_mats]
            return [parent2world_matrix @ mat for mat in link2base_mats]
        return None

    def get_collision_local2world_mats(self, parent2world_matrix: Optional[Matrix] = None) -> Optional[List[Matrix]]:
        """Returns the transformation matrices from world to the collision parts.

        :param parent2world_matrix: The transformation from the link's armature to the world frame.
        :return: List of transformation matrices.
        """
        bpy.context.view_layer.update()
        if parent2world_matrix is None:
            parent2world_matrix = Matrix(Entity(self.armature).get_local2world_mat())
        bone_mat = Matrix.Identity(4)
        if self.bone is not None:
            bone_mat = self.bone.matrix
        if self.collisions:
            link2base_mats = [bone_mat @ (self.link2bone_mat.inverted() @ collision_local2link_mat) for
                              collision_local2link_mat in self.collision_local2link_mats]
            return [parent2world_matrix @ mat for mat in link2base_mats]
        return None

    def get_inertial_local2world_mat(self, parent2world_matrix: Optional[Matrix] = None) -> Optional[Matrix]:
        """Returns the transformation matrix from world to the inertial part.

        :param parent2world_matrix: The transformation from the link's armature to the world frame.
        :return: The transformation matrix.
        """
        bpy.context.view_layer.update()
        if parent2world_matrix is None:
            parent2world_matrix = Matrix(Entity(self.armature).get_local2world_mat())
        bone_mat = Matrix.Identity(4)
        if self.bone is not None:
            bone_mat = self.bone.matrix
        if self.inertial is not None:
            link2base_mat = bone_mat @ (self.link2bone_mat.inverted() @ self.inertial_local2link_mat)
            return parent2world_matrix @ link2base_mat
        return None

    def get_all_objs(self):
        """ Returns all meshes of this link.

        :return: List of all meshes (visual, collision, inertial) for this link.
        """
        return self.visuals + self.collisions + ([self.inertial] if self.inertial is not None else [])

    def set_joint_type(self, joint_type: Optional[str]):
        """ Sets the joint type of the link which specifies the connection to its parent.

        :param joint_type: One of ['fixed', 'prismatic', 'revolute', 'continuous', 'planar', 'floating' or None].
        """
        object.__setattr__(self, "joint_type", joint_type)

    def get_joint_type(self) -> Optional[str]:
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

    def create_ik_bone_controller(self, relative_location: Optional[Union[List[float], Vector]] = None,
                                   use_rotation: bool = True,
                                   chain_length: int = 0) -> Tuple[bpy.types.PoseBone, bpy.types.PoseBone, Matrix]:
        """ Creates an ik bone controller and a corresponding constraint bone for the respective link.

        :param relative_location: Relative location of the ik bone controller w.r.t. the bone's location. This can be
                                  used to shift the point of control further away from the end effector.
        :param use_rotation: Whether to rotate the child links as well. Defaults to True.
        :param chain_length: The number of parent links which are influenced by this ik bone. Defaults to 0 for all
                             parents.
        :return: Constraint and control bone.
        """

        if relative_location is None:
            relative_location = [0., 0., 0.]

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
        """ Returns the currently selected mode.

        :return: One of ["fk", "ik"] denoting forward or inverse kinematics mode.
        """
        return self.fk_ik_mode

    def switch_fk_ik_mode(self, mode: str = "fk", keep_pose: bool = True):
        """ Switches between forward and inverse kinematics mode. Will do this automatically when switching between e.g.
            `set_rotation_euler_fk()` and `set_rotation_euler_ik()`.

        :param mode: One of ["fk", "ik"] denoting forward or inverse kinematics mode.
        :param keep_pose: If specified, will keep the pose when switching modes. Otherwise, will return to the old pose
                          of the previously selected mode.
        """
        if self.bone is None:
            return None
        assert mode in ["fk", "ik"]
        if mode == "fk":  # turn off copy rotation constraints of fk bone and base bone
            if self.get_fk_ik_mode() == "fk":
                return None
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
                return None
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
        return None

    def get_joint_rotation(self, frame: int = None) -> float:
        """ Get current joint rotation based on euler angles.

        :param frame: The desired frame.
        :return: Current joint rotation in radians.
        """

        if self.bone is None:
            return 0.0

        pose_bone = self.armature.pose.bones[self.bone.name]
        data_bone = self.armature.data.bones[self.bone.name]

        with KeyFrame(frame):
            M_pose = pose_bone.matrix
            M_data = data_bone.matrix_local

        # grab the parent's world pose and rest matrices
        if data_bone.parent:
            M_parent_data = data_bone.parent.matrix_local.copy()
            M_parent_pose = pose_bone.parent.matrix.copy()
        else:
            M_parent_data = Matrix()
            M_parent_pose = Matrix()

        M1 = M_data.copy()
        M1.invert()

        M2 = M_parent_pose.copy()
        M2.invert()

        visual_matrix = M1 @ M_parent_data @ M2 @ M_pose

        return visual_matrix.to_quaternion().angle

    def mesh_as_trimesh(self) -> Optional[Trimesh]:
        """ Returns a trimesh.Trimesh instance of the link's first visual object, if it exists.

        :return: The link's first visual object as trimesh.Trimesh if the link has one or more visuals, else None.
        """
        # get mesh data
        if self.visuals:
            return self.visuals[0].mesh_as_trimesh()

        return None

# pylint: enable=no-member
