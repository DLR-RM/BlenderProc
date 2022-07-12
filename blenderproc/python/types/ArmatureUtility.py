from typing import Union, List, Optional
import numpy as np
from mathutils import Euler, Vector

import bpy

from blenderproc.python.utility.Utility import Utility
from blenderproc.python.types.EntityUtility import Entity


class Armature(Entity):
    def __init__(self, bpy_object: bpy.types.Object):
        super().__init__(bpy_object=bpy_object)

    def set_rotation_euler(self, rotation_euler: Union[float, list, Euler, np.ndarray], mode: str = "absolute", frame: int = None):
        """ Rotates the armature based on euler angles. Validates values with given constraints.

        :param rotation_euler: The amount of rotation (in radians). Either three floats for x, y and z axes, or a single float.
                               In the latter case, the axis of rotation is derived based on the rotation constraint. If
                               these are not properly set (i.e., two axes must have equal min/max values) an exception will be thrown.
        :param mode: One of ["absolute", "relative"]. For absolute rotations we clip the rotation value based on the constraints.
                     For relative we don't - this will result in inverse motion after the constraint's limits have been reached.
        :param frame: Keyframe where to insert the respective rotations.
        """
        assert mode in ["absolute", "relative"]
        bpy.ops.object.select_all(action='DESELECT')
        bone = self.blender_obj.pose.bones.get('Bone')
        bone.bone.select = True
        bone.rotation_mode = 'XYZ'

        # in absolute mode we overwrite the rotation values of the armature
        if mode == "absolute":
            if isinstance(rotation_euler, float):
                axis = self._determine_rotation_axis()
                rotation_euler = self._clip_value_from_constraint(value=rotation_euler, constraint_name="Limit Rotation", axis=axis)
                current_rotation_euler = bone.rotation_euler
                current_rotation_euler[["X", "Y", "Z"].index(axis)] = rotation_euler
                bone.rotation_euler = current_rotation_euler
                print(f"Set rotation_euler of armature {self.get_name()} to {rotation_euler}")
            else:
                bone.rotation_euler = Vector([self._clip_value_from_constraint(value=rot_euler, constraint_name="Limit Rotation", axis=axis)
                                              for rot_euler, axis in zip(rotation_euler, ["X", "Y", "Z"])])
                print(f"Set rotation_euler of armature {self.get_name()} to {rotation_euler}")
        # in relative mode we add the rotation to the current value
        elif mode == "relative":
            if isinstance(rotation_euler, float):
                axis = self._determine_rotation_axis()
                bone.rotation_euler.rotate_axis(axis, rotation_euler)
                print(f"Relatively rotated armature {self.get_name()} around axis {axis} for {rotation_euler} radians")
            else:
                for axis, rotation in zip(["X", "Y", "Z"], rotation_euler):
                    bone.rotation_euler.rotate_axis(axis, rotation)
                print(f"Relatively rotated armature {self.get_name()} for {rotation_euler} radians")

        Utility.insert_keyframe(bone, "rotation_euler", frame)
        if frame is not None and frame > bpy.context.scene.frame_end:
            bpy.context.scene.frame_end += 1

    def _determine_rotation_axis(self):
        """ Determines the single rotation axis and checks if the constraints are set well to have only one axis of freedom.

        :return: The single rotation axis ('X', 'Y' or 'Z').
        """
        c = self.get_constraint(constraint_name="Limit Rotation")
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

    def _clip_value_from_constraint(self, value: float, constraint_name: str, axis: str) -> float:
        """ Checks if an axis is constraint, and clips the value to the min/max of this constraint. If the constraint does not exist, nothing is done.

        :param value: Value to be clipped.
        :param constraint_name: Name of the constraint.
        :param axis: Axis to check.
        :return: Clipped value if a constraint is set, else the initial value.
        """
        c = self.get_constraint(constraint_name=constraint_name)
        if c is not None:
            min_value = eval(f"c.min_{axis.lower()}")
            max_value = eval(f"c.max_{axis.lower()}")
            print(f"Clipping {value} to be in range {min_value}, {max_value}")
            if value < min_value:
                return min_value
            elif value > max_value:
                return max_value
        return value

    def add_constraint_if_not_existing(self, constraint_name: str) -> bpy.types.Constraint:
        """ Adds a new constraint if it doesn't exist, and returns the specified constraint.

        :param constraint_name: Name of the desired constraint.
        """
        if constraint_name not in self.blender_obj.pose.bones["Bone"].constraints.keys():
            self.blender_obj.pose.bones["Bone"].constraints.new(constraint_name.upper().replace(' ', '_'))
        return self.blender_obj.pose.bones["Bone"].constraints[constraint_name]

    def set_rotation_constraint(self, x_limits: Optional[List[float]] = None, y_limits: Optional[List[float]] = None, z_limits: Optional[List[float]] = None):
        """ Sets rotation constraints on the armature's bone.

        :param x_limits: A list of two float values specifying min/max radiant values along the x-axis or None if no constraint should be applied.
        :param y_limits: A list of two float values specifying min/max radiant values along the y-axis or None if no constraint should be applied.
        :param z_limits: A list of two float values specifying min/max radiant values along the z-axis or None if no constraint should be applied.
        """
        if x_limits is None and y_limits is None and z_limits is None:
            return

        # add new constraint if it doesn't exist
        constraint = self.add_constraint_if_not_existing(constraint_name="Limit Rotation")

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

    def set_location_constraint(self, x_limits: Optional[List[float]] = None, y_limits: Optional[List[float]] = None, z_limits: Optional[List[float]] = None):
        """ Sets location constraints on the armature's bone.

        :param x_limits: A list of two float values specifying min/max values along the x-axis or None if no constraint should be applied.
        :param y_limits: A list of two float values specifying min/max values along the y-axis or None if no constraint should be applied.
        :param z_limits: A list of two float values specifying min/max values along the z-axis or None if no constraint should be applied.
        """
        if x_limits is None and y_limits is None and z_limits is None:
            return

        # add new constraint if it doesn't exist
        constraint = self.add_constraint_if_not_existing(constraint_name="Limit Location")

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

    def get_constraint(self, constraint_name: str) -> Optional[bpy.types.Constraint]:
        """ Returns the desired constraint if existing; otherwise None.

        :param constraint_name: Name of the constraint.
        :return: Constraint if it exists; else None.
        """
        if constraint_name in self.blender_obj.pose.bones["Bone"].constraints.keys():
            return self.blender_obj.pose.bones["Bone"].constraints[constraint_name]
        return None

    def get_location_constraint(self) -> Optional[bpy.types.Constraint]:
        """ Returns the location constraint if existing; otherwise None.

        :return: Location constraint if it exists; else None.
        """
        return self.get_constraint(constraint_name="Limit Location")

    def get_rotation_constraint(self) -> Optional[bpy.types.Constraint]:
        """ Returns the rotation constraint if existing; otherwise None.

        :return: Rotation constraint if it exists; else None.
        """
        return self.get_constraint(constraint_name="Limit Rotation")

    def remove_constraint(self, constraint_key: str):
        """ Removes a specified constraint.

        :param constraint_key: Key to be removed.
        """
        bone = self.blender_obj.pose.bones["Bone"]
        bone.constraints.remove(bone.constraints[constraint_key])

    def remove_constraints(self):
        """ Removes all constraints of the armature. """
        bone = self.blender_obj.pose.bones["Bone"]
        for constraint_key in bone.constraints.keys():
            self.remove_constraint(constraint_key=constraint_key)

    def hide(self, hide_object: bool = True):
        """ Sets the visibility of the object.

        :param hide_object: Determines whether the object should be hidden in rendering.
        """
        self.blender_obj.hide_render = hide_object
