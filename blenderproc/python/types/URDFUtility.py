from typing import Union, List
import numpy as np

import bpy

from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.ArmatureUtility import Armature
from typing import Union, List
import numpy as np
from mathutils import Vector, Euler, Color, Matrix, Quaternion

import bpy

from blenderproc.python.utility.Utility import Utility
from blenderproc.python.types.EntityUtility import Entity


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


class Link(Entity):
    def __init__(self, bpy_object):
        super().__init__(bpy_object)
        object.__setattr__(self, 'visuals', [])
        object.__setattr__(self, 'inertial', None)
        object.__setattr__(self, 'collisions', [])
        object.__setattr__(self, 'joint_type', None)
        object.__setattr__(self, 'bone', None)
        object.__setattr__(self, 'bone_rot_vec', None)  # unit vector of axis of rotation; used to compare to ik pose
        object.__setattr__(self, 'ik_bone', None)
        object.__setattr__(self, 'fk_bone', None)
        object.__setattr__(self, '_ik_bone_offset', Vector([0., 0., 0.]))
        object.__setattr__(self, 'armature', None)
        object.__setattr__(self, 'fk_ik_mode', "fk")

    def set_rotation_euler(self, rotation_euler: Union[float, list, Euler, np.ndarray], mode: str = "absolute",
                           frame: int = 0):
        """ Rotates the armature based on euler angles. Validates values with given constraints.

        :param rotation_euler: The amount of rotation (in radians). Either three floats for x, y and z axes, or a single float.
                               In the latter case, the axis of rotation is derived based on the rotation constraint. If
                               these are not properly set (i.e., two axes must have equal min/max values) an exception will be thrown.
        :param mode: One of ["absolute", "relative"]. For absolute rotations we clip the rotation value based on the constraints.
                     For relative we don't - this will result in inverse motion after the constraint's limits have been reached.
        :param frame: Keyframe where to insert the respective rotations.
        """
        assert mode in ["absolute", "relative"]
        if self.fk_ik_mode == "ik":
            self._switch_fk_ik_mode(mode="fk")
        bpy.ops.object.select_all(action='DESELECT')
        # bone = self.blender_obj.pose.bones.get('Bone')
        self.fk_bone.bone.select = True
        self.fk_bone.rotation_mode = 'XYZ'

        # in absolute mode we overwrite the rotation values of the armature
        if mode == "absolute":
            if isinstance(rotation_euler, float):
                axis = self._determine_rotation_axis(bone=self.fk_bone)
                rotation_euler = self._clip_value_from_constraint(bone=self.fk_bone, value=rotation_euler,
                                                                  constraint_name="Limit Rotation", axis=axis)
                current_rotation_euler = self.fk_bone.rotation_euler
                current_rotation_euler[["X", "Y", "Z"].index(axis)] = rotation_euler
                self.bone.rotation_euler = current_rotation_euler
                print(f"Set rotation_euler of armature {self.get_name()} to {rotation_euler}")
            else:
                self.bone.rotation_euler = Vector(
                    [self._clip_value_from_constraint(bone=self.fk_bone, value=rot_euler,
                                                      constraint_name="Limit Rotation", axis=axis)
                     for rot_euler, axis in zip(rotation_euler, ["X", "Y", "Z"])])
                print(f"Set rotation_euler of armature {self.get_name()} to {rotation_euler}")
        # in relative mode we add the rotation to the current value
        elif mode == "relative":
            if isinstance(rotation_euler, float):
                axis = self._determine_rotation_axis(bone=self.fk_bone)
                self.fk_bone.rotation_euler.rotate_axis(axis, rotation_euler)
                print(f"Relatively rotated armature {self.get_name()} around axis {axis} for {rotation_euler} radians")
            else:
                for axis, rotation in zip(["X", "Y", "Z"], rotation_euler):
                    self.fk_bone.rotation_euler.rotate_axis(axis, rotation)
                print(f"Relatively rotated armature {self.get_name()} for {rotation_euler} radians")

        Utility.insert_keyframe(self.fk_bone, "rotation_euler", frame)
        if frame > bpy.context.scene.frame_end:
            bpy.context.scene.frame_end += 1

    def set_location(self, location):
        assert self.ik_bone is not None, f"No ik bone chain created. Please run 'self.create_ik_bone()' first!"
        if self.fk_ik_mode == "fk":
            self._switch_fk_ik_mode(mode="ik")
        bpy.ops.object.select_all(action='DESELECT')
        self.ik_bone.bone.select = True
        mat = Matrix(np.array([self.ik_bone.x_axis, self.ik_bone.y_axis, self.ik_bone.z_axis]).T)
        self.ik_bone.location = (mat @ self.ik_bone.head) - (mat @ self._ik_bone_offset) + (location @ mat)
        bpy.context.view_layer.update()

    def _determine_rotation_axis(self, bone=None):
        """ Determines the single rotation axis and checks if the constraints are set well to have only one axis of freedom.

        :return: The single rotation axis ('X', 'Y' or 'Z').
        """
        c = self.get_constraint(bone=bone, constraint_name="Limit Rotation")
        assert c is not None, f"Tried to determine the single rotation axis but no rotation constraints are set!"

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

    def _clip_value_from_constraint(self, bone=None, value: float = 0, constraint_name: str = "",
                                    axis: str = "X") -> float:
        """ Checks if an axis is constraint, and clips the value to the min/max of this constraint. If the constraint does not exist, nothing is done.

        :param value: Value to be clipped.
        :param constraint_name: Name of the constraint.
        :param axis: Axis to check.
        :return: Clipped value if a constraint is set, else the initial value.
        """
        c = self.get_constraint(bone=bone, constraint_name=constraint_name)
        if c is not None:
            min_value = eval(f"c.min_{axis.lower()}")
            max_value = eval(f"c.max_{axis.lower()}")
            print(f"Clipping {value} to be in range {min_value}, {max_value}")
            if value < min_value:
                return min_value
            elif value > max_value:
                return max_value
        return value

    def add_constraint_if_not_existing(self, bone=None, constraint_name: str = "", custom_constraint_name: str = "",
                                       add_to_existing: bool = False) -> bpy.types.Constraint:
        """ Adds a new constraint.

        :param constraint_name: Name of the desired constraint.
        """
        if bone is None:
            bone = self.bone
        if custom_constraint_name == "":
            custom_constraint_name = constraint_name
        if constraint_name not in bone.constraints.keys() or add_to_existing:
            c = bone.constraints.new(constraint_name.upper().replace(' ', '_'))
            c.name = custom_constraint_name
            return c
        else:
            return None

    def set_rotation_constraint(self, bone=None, x_limits: Union[List[float], None] = None,
                                y_limits: Union[List[float], None] = None, z_limits: Union[List[float], None] = None,
                                set_ik_limits: bool = True):
        """ Sets rotation constraints on the armature's bone.

        :param x_limits: A list of two float values specifying min/max radiant values along the x-axis or None if no constraint should be applied.
        :param y_limits: A list of two float values specifying min/max radiant values along the y-axis or None if no constraint should be applied.
        :param z_limits: A list of two float values specifying min/max radiant values along the z-axis or None if no constraint should be applied.
        """
        if x_limits is None and y_limits is None and z_limits is None:
            return

        if bone is None:
            bone = self.bone

        # add new constraint if it doesn't exist
        constraint = self.add_constraint_if_not_existing(bone, constraint_name="Limit Rotation")

        if x_limits is not None:
            constraint.use_limit_x = True
            constraint.min_x, constraint.max_x = x_limits
        if y_limits is not None:
            constraint.use_limit_y = True
            constraint.min_y, constraint.max_y = y_limits
        if z_limits is not None:
            constraint.use_limit_z = True
            constraint.min_z, constraint.max_z = z_limits
        constraint.owner_space = "LOCAL"

        if set_ik_limits:
            self.set_ik_limits_from_rotation_constraint()  # todo try if necessary

    def set_ik_limits_from_rotation_constraint(self, bone=None):
        if bone is None:
            bone = self.bone
        c = self.get_rotation_constraint(bone=bone)

        if c is not None:
            if c.use_limit_x:
                if c.min_x == c.max_x == 0:
                    bone.lock_ik_x = True
                else:
                    bone.use_ik_limit_x = True
                    bone.ik_min_x = c.min_x
                    bone.ik_max_x = c.max_x
            if c.use_limit_y:
                if c.min_y == c.max_y == 0:
                    bone.lock_ik_y = True
                else:
                    bone.use_ik_limit_y = True
                    bone.ik_min_y = c.min_y
                    bone.ik_max_y = c.max_y
            if c.use_limit_z:
                if c.min_z == c.max_z == 0:
                    bone.lock_ik_z = True
                else:
                    bone.use_ik_limit_z = True
                    bone.ik_min_z = c.min_z
                    bone.ik_max_z = c.max_z

    def copy_constraints(self, source_bone, target_bone, constraints_to_be_copied=[]):
        # constraints_to_be_copied = [c.upper().replace(' ', '_') for c in constraints_to_be_copied]
        for c in source_bone.constraints:
            print(c.name, constraints_to_be_copied)
            if constraints_to_be_copied != [] and c.name not in constraints_to_be_copied:
                continue
            c_copy = self.add_constraint_if_not_existing(target_bone, constraint_name=c.name)
            for prop in dir(c):
                try:
                    setattr(c_copy, prop, getattr(c, prop))
                except:
                    pass

    def set_ik_constraint(self):
        target_bone_name = self.bone.name + '.ik'
        c = self.add_constraint_if_not_existing(self.armature.pose.bones[target_bone_name], constraint_name="IK")
        c.target = self.armature
        print("ik bone name", self.ik_bone.name)
        c.subtarget = self.ik_bone.name

    def set_copy_rotation_constraint(self, bone=None, target_bone="", custom_constraint_name=""):
        c = self.add_constraint_if_not_existing(bone, constraint_name="Copy Rotation",
                                                custom_constraint_name=custom_constraint_name, add_to_existing=True)
        c.target = self.armature
        c.subtarget = target_bone
        print("ASDFASDFASFD", c.target, c.subtarget)

    def set_location_constraint(self, bone=None, x_limits: Union[List[float], None] = None,
                                y_limits: Union[List[float], None] = None, z_limits: Union[List[float], None] = None):
        """ Sets location constraints on the armature's bone.

        :param x_limits: A list of two float values specifying min/max values along the x-axis or None if no constraint should be applied.
        :param y_limits: A list of two float values specifying min/max values along the y-axis or None if no constraint should be applied.
        :param z_limits: A list of two float values specifying min/max values along the z-axis or None if no constraint should be applied.
        """
        if x_limits is None and y_limits is None and z_limits is None:
            return

        if bone is None:
            bone = self.bone

        # add new constraint if it doesn't exist
        constraint = self.add_constraint_if_not_existing(bone, constraint_name="Limit Location")

        if x_limits is not None:
            constraint.use_min_x = True
            constraint.use_max_x = True
            constraint.min_x, constraint.max_x = x_limits
        if y_limits is not None:
            constraint.use_min_y = True
            constraint.use_max_y = True
            constraint.min_y, constraint.max_y = y_limits
        if z_limits is not None:
            constraint.use_min_z = True
            constraint.use_max_z = True
            constraint.min_z, constraint.max_z = z_limits
        constraint.owner_space = "LOCAL"

    def get_constraint(self, bone=None, constraint_name: str = "") -> Union[bpy.types.Constraint, None]:
        """ Returns the desired constraint if existing; otherwise None.

        :param constraint_name: Name of the constraint.
        :return: Constraint if it exists; else None.
        """
        if bone is None:
            bone = self.bone
        if constraint_name in bone.constraints.keys():
            return bone.constraints[constraint_name]
        return None

    def get_location_constraint(self, bone=None) -> Union[bpy.types.Constraint, None]:
        """ Returns the location constraint if existing; otherwise None.

        :return: Location constraint if it exists; else None.
        """
        if bone is None:
            bone = self.bone
        return self.get_constraint(bone, constraint_name="Limit Location")

    def get_rotation_constraint(self, bone=None) -> Union[bpy.types.Constraint, None]:
        """ Returns the rotation constraint if existing; otherwise None.

        :return: Rotation constraint if it exists; else None.
        """
        if bone is None:
            bone = self.bone
        return self.get_constraint(bone, constraint_name="Limit Rotation")

    def remove_constraint(self, bone=None, constraint_key: str = ""):
        """ Removes a specified constraint.

        :param constraint_key: Key to be removed.
        """
        if bone is None:
            bone = self.bone
        bone.constraints.remove(self.bone.constraints[constraint_key])

    def remove_constraints(self, bone=None):
        """ Removes all constraints of the armature. """
        if bone is None:
            bone = self.bone
        for constraint_key in bone.constraints.keys():
            self.remove_constraint(bone=bone, constraint_key=constraint_key)

    def set_visuals(self, visuals):
        object.__setattr__(self, "visuals", visuals)

    def set_collisions(self, collisions):
        object.__setattr__(self, "collisions", collisions)

    def set_inertial(self, inertial):
        object.__setattr__(self, "inertial", inertial)

    def set_bone(self, bone):
        object.__setattr__(self, "bone", bone)

    def set_ik_bone(self, bone):
        object.__setattr__(self, "ik_bone", bone)

    def set_fk_bone(self, bone):
        object.__setattr__(self, "fk_bone", bone)

    def set_armature(self, armature):
        object.__setattr__(self, "armature", armature)

    def set_fk_ik_mode(self, mode="fk"):
        object.__setattr__(self, "fk_ik_mode", mode)

    def get_all_objects(self):
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

    def parent_with_bone(self, weight_distribution='envelope'):
        assert weight_distribution in ['envelope', 'automatic', 'rigid']
        # armature = get_armature_from_bone(self.bone.name)

        if self.bone is None:
            # only set parent
            print(f"WARNING: Link {self.get_name()} does not have a bone to be parented with!")
            self.blender_obj.parent = self.armature
            return

        if weight_distribution in ['envelope', 'automatic']:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
            # for link in links:
            #    link.select()
            self.select()
            for obj in self.get_all_objects():
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
            for obj in self.get_all_objects() + [self]:
                bpy.ops.object.select_all(action='DESELECT')
                obj.blender_obj.parent = self.armature
                bpy.context.view_layer.objects.active = obj.blender_obj
                mod = obj.blender_obj.modifiers.new("Armature", "ARMATURE")  # todo other name than "Armature"?
                mod.object = self.armature
                obj.blender_obj.vertex_groups.new(name=self.bone.name)
                vertices = [v.index for v in obj.blender_obj.data.vertices]
                obj.blender_obj.vertex_groups[0].add(vertices, 1.0, 'REPLACE')
        bpy.ops.object.select_all(action='DESELECT')

    def create_ik_bone(self, offset=[0., 1., 0.], chain_length=0, start_bone=None, leave_following_untouched=False):
        object.__setattr__(self, "_ik_bone_offset", Vector(offset))
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        self.armature.select_set(True)
        # determine all bones to copy

        bpy.context.view_layer.objects.active = self.armature
        parent_bones = self.bone.parent_recursive
        if start_bone is not None:
            parent_bone_names = [b.name for b in parent_bones]
            if start_bone not in parent_bone_names:
                print(
                    f"Provided a start_bone {start_bone.name}, but this bone is not in the parent bones of the selected bone {self.bone.name}. Using no start bone!")
            elif start_bone == parent_bone_names[-1]:
                print(f"Cannot start from base frame as the first ik bone needs to have a parent!")
            else:
                parent_bones = parent_bones[:parent_bone_names.index(start_bone) + 2]
        parent_bones.insert(0, self.bone)
        print("types", parent_bones[0], parent_bones[-1])
        for parent_bone in parent_bones:
            print(parent_bone.name)
        # copy bones
        edit_bones = self.armature.data.edit_bones
        parent_name = parent_bones.pop(-1).name
        base_name = parent_name

        for parent_bone in parent_bones[::-1]:
            # bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='EDIT')
            self.armature.select_set(True)
            print(f"Creating ik bone for {parent_bone.name}")
            name = parent_bone.name + '.ik'  # + self.get_name()
            editbone = edit_bones.new(name)
            editbone.head = parent_bone.head + Vector(offset)
            editbone.tail = parent_bone.tail + Vector(offset)
            last_pose = Vector(editbone.tail)  # copy otherwise this will reset because of mode switch below

            if parent_name is not None:
                editbone.parent = edit_bones[parent_name]
                print(f"setting", parent_name, "as parent of", editbone.name)

            parent_name = name

        bpy.ops.object.mode_set(mode='POSE')
        for parent_bone in parent_bones[::-1]:
            name = parent_bone.name + '.ik'  # + self.get_name()

            # add constraints; this has to be done for a pose bone
            self.copy_constraints(self.armature.pose.bones[parent_bone.name],
                                  self.armature.pose.bones[name],
                                  constraints_to_be_copied=["Limit Rotation", "Limit Location"])
            # self.copy_constraints(, self.armature.pose.bones[name], constraints_to_be_copied=["Limit Rotation"])
            # copy the rotation of the bone
            self.set_copy_rotation_constraint(bone=self.armature.pose.bones[parent_bone.name], target_bone=name,
                                              custom_constraint_name="copy_rotation.ik")

            # fk bones should mimic jk bones, and vice versa
            print("at", parent_bone.name)
            self.set_copy_rotation_constraint(bone=self.armature.pose.bones[parent_bone.name + '.fk'], target_bone=name,
                                              custom_constraint_name="copy_rotation.ik")
            self.set_copy_rotation_constraint(bone=self.armature.pose.bones[parent_bone.name + '.ik'],
                                              target_bone=parent_bone.name + '.fk',
                                              custom_constraint_name="copy_rotation.fk")

            self.set_ik_limits_from_rotation_constraint(bone=self.armature.pose.bones[name])
            # bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # add ik bone
        bpy.ops.object.mode_set(mode='EDIT')
        print("after", last_pose)
        ik_bone = edit_bones.new(self.get_name() + '.ik')
        ik_bone.head = last_pose
        ik_bone.tail = ik_bone.head + Vector([0., 0., 0.2])
        ik_bone.parent = edit_bones[base_name]
        bpy.ops.object.mode_set(mode='POSE')
        self.set_ik_bone(self.armature.pose.bones.get(self.get_name() + '.ik'))

        # remove location constraint for revolute joints

        # add ik constraint

        self.set_ik_constraint()

        # add copy_rotation constraint for revolute joints

        bpy.ops.object.mode_set(mode='OBJECT')

    def get_fk_ik_mode(self):
        return self.fk_ik_mode

    def _switch_fk_ik_mode(self, mode="fk", keep_pose=True):
        if self.bone is None:
            return
        assert mode in ["fk", "ik"]
        if mode == "fk":  # turn off copy rotation constraints of fk bone and base bone
            from copy import copy
            mat = copy(Matrix(self.fk_bone.matrix))
            print("mat in fk", mat)
            if self.ik_bone is not None:  # switch off ik constraint
                self.armature.pose.bones[self.bone.name + ".ik"].constraints["IK"].influence = 0.

            if "copy_rotation.ik" in self.bone.constraints.keys():
                self.bone.constraints["copy_rotation.ik"].influence = 0.  # otherwise skip
            self.bone.constraints["copy_rotation.fk"].influence = 1.
            if "copy_rotation.ik" in self.fk_bone.constraints.keys():
                self.fk_bone.constraints["copy_rotation.ik"].influence = 0.
            if self.bone.name + ".ik" in self.armature.pose.bones.keys():  # otherwise skip
                self.armature.pose.bones[self.bone.name + ".ik"].constraints["copy_rotation.fk"].influence = 1.
            if keep_pose:
                self.fk_bone.matrix = mat
            self.set_fk_ik_mode(mode="fk")
            print("fk mat", self.get_name(), mat)
        else:  # turn off copy rotation constraints of ik bone and base bone
            from copy import copy
            # bpy.ops.object.mode_set(mode='OBJECT')
            # bpy.ops.object.select_all(action='DESELECT')
            # self.armature.select_set(True)
            # bpy.ops.object.mode_set(mode='POSE')
            mat = copy(Matrix(self.fk_bone.matrix))

            print("mat before", mat)

            if "copy_rotation.ik" in self.bone.constraints.keys():
                self.bone.constraints["copy_rotation.ik"].influence = 1.  # otherwise skip
            self.bone.constraints["copy_rotation.fk"].influence = 0.
            if "copy_rotation.ik" in self.fk_bone.constraints.keys():
                self.fk_bone.constraints["copy_rotation.ik"].influence = 1.
            if self.bone.name + ".ik" in self.armature.pose.bones.keys():  # otherwise skip
                self.armature.pose.bones[self.bone.name + ".ik"].constraints["copy_rotation.fk"].influence = 0.
            if keep_pose and self.bone.name + ".ik" in self.armature.pose.bones.keys():
                # keys = [k for k in self.armature.pose.bones.keys() if k.startswith(self.bone.name + '.ik')]
                # print("found keys:", keys)
                # if keys != []:
                #    for key in keys:
                self.armature.pose.bones[self.bone.name + ".ik"].matrix = mat
                print("set to", mat)
            # shift ik bone to tail of previous bone
            self.set_fk_ik_mode(mode="ik")
            if self.ik_bone is not None:
                print("got ik link", self.get_name(), self.ik_bone.name, self.bone.name)
                print("tail of ik bone")
                # bpy.ops.object.mode_set(mode='POSE')

                # location = self.armature.data.edit_bones[self.bone.name + ".ik"].tail
                mat = np.array(self.armature.pose.bones[self.bone.name].matrix)
                location = Vector(np.array(mat)[:3, -1])

                # add tail offset
                tail_offset = np.array(self.armature.pose.bones[self.bone.name].tail) - np.array(
                    self.armature.pose.bones[self.bone.name].head)
                location += Vector(tail_offset)
                print(location)
                print("mat", mat)
                # bpy.ops.object.mode_set(mode='OBJECT')
                self.set_location(location)
            if self.ik_bone is not None:  # switch on ik constraint, and move ik bone. important to do this AFTER setting matrix of ik link
                self.armature.pose.bones[self.bone.name + ".ik"].constraints["IK"].influence = 1.
            bpy.ops.object.mode_set(mode='OBJECT')


class URDFObject(Entity):
    def __init__(self, armature: bpy.types.Armature, links: List[Link], xml_tree: Union["urdfpy.URDF", None] = None):
        super().__init__(bpy_object=armature)  # allows full manipulation (translation, scale, rotation) of whole urdf object
        object.__setattr__(self, "links", links)
        object.__setattr__(self, "xml_tree", xml_tree)

    def get_all_urdf_objs(self) -> List[Union[Link, Inertial, MeshObject]]:
        """ Returns a list of all urdf-related objects.

        :return: List of all urdf-related objects.
        """
        objs = []
        for link in self.links:
            objs.append(link)
            objs.extend(link.get_children())
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
        self.hide()
        for link in self.links:
            link.hide()
            for child in link.blender_obj.children:
                if isinstance(child, bpy.types.Object):
                    child = MeshObject(child)
                if 'collision' in child.get_name() or 'inertial' in child.get_name():
                    child.hide()

    def set_ascending_category_ids(self, category_ids: Union[List[int], None] = None):
        """ Sets semantic categories to the links and their associated objects.

        :param category_ids: List of 'category_id's for every link. If None, will create a list from [1 ... len(links)].
        """
        if category_ids is None:
            category_ids = list(range(1, len(self.links) + 1))

        assert len(category_ids) == len(self.links), f"Need equal amount of category ids for links. Got {len(category_ids)} and {len(self.links)}, respectively."
        for link, category_id in zip(self.links, category_ids):
            link.set_cp(key="category_id", value=category_id)
            for obj in link.get_children():
                obj.set_cp(key="category_id", value=category_id)

    def remove_link_by_index(self, index: int = 0):
        """ Removes a link and all its associated objects given an index. Also handles relationship of the link's child with its parent.
        This is useful for removing a 'world link' which could be a simple flat surface, or if someone wants to shorten the whole urdf object.

        :param index: Index of the joint to be removed.
        """
        assert index < len(self.links), f"Invalid index {index}. Index must be in range 0, {len(self.links)} (no. links: {len(self.links)})."

        # remove link from the urdf instance and determine child / parent
        parent = self.links[index - 1] if index != 0 else None
        child = self.links[index + 1] if index != len(self.links) else None
        link_to_be_removed = self.links.pop(index)

        # calculate new transformation of child and set new parent
        if child is not None:
            child.blender_obj.matrix_world = link_to_be_removed.blender_obj.matrix_world
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, properties=True)

            # handle new parent-child relationship
            if parent is not None:
                bpy.ops.object.select_all(action='DESELECT')
                parent.select()
                child.select()

                # select which object to parent to
                bpy.context.view_layer.objects.active = parent.blender_obj

                # parent object
                bpy.ops.object.posemode_toggle()
                bpy.ops.object.parent_set(type="BONE")
                bpy.ops.object.posemode_toggle()

        # set new base in case the original base will be removed
        if index == 0:
            super().__init__(bpy_object=self.links[0].blender_obj)

        # finally, delete the link and all its children
        for obj in link_to_be_removed.get_children():
            obj.delete()
        link_to_be_removed.delete()

    def set_name(self, name: str):
        """ Sets the name of the urdf object.

        :param name: The new name.
        """
        self.name = name

    def get_name(self) -> str:
        """ Returns the name of the urdf object.

        :return: The name.
        """
        return self.name

    def hide(self, hide_object: bool = True):
        """ Sets the visibility of the object.

        :param hide_object: Determines whether the object should be hidden in rendering.
        """
        for link in self.links:
            link.hide(hide_object=hide_object)
            for child in link.get_children():
                child.hide(hide_object=hide_object)

    def get_all_local2world_mats(self):
        """ Returns all matrix_world matrices from every joint. """

        return np.stack([link.blender_obj.matrix_world for link in self.links])
