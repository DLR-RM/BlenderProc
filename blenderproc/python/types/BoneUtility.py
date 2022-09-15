""" Utility functions to manage the connections between nodes. """

from typing import List, Optional

import bpy

from blenderproc.python.types.MeshObjectUtility import MeshObject


def get_armature_from_bone(bone_name: str) -> Optional[MeshObject]:
    """ Returns the armature that holds a specified bone.

    :param bone_name: Name of the bone.
    :return: The respective armature.
    """
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            if obj.pose.bones.get(bone_name) is not None:
                return obj
    return None


def add_constraint_if_not_existing(bone: bpy.types.PoseBone, constraint_name: str = "",
                                   custom_constraint_name: Optional[str] = None,
                                   add_to_existing: bool = False) -> Optional[bpy.types.Constraint]:
    """ Adds a new constraint.

    :param bone: The bone to add the constraint to.
    :param constraint_name: Name of the desired constraint.
    :param custom_constraint_name: Custom name for the constraint. If not specified will use the default name.
    :param add_to_existing: If true, will add a new constraint even if a constraint of the same type already exists.
    :return: The created constraint or None if it already exists and `add_to_existing=False`.
    """
    if custom_constraint_name is None:
        custom_constraint_name = constraint_name
    if constraint_name not in bone.constraints.keys() or add_to_existing:
        c = bone.constraints.new(constraint_name.upper().replace(' ', '_'))
        c.name = custom_constraint_name
        return c
    return None


def set_rotation_constraint(bone: bpy.types.PoseBone, x_limits: Optional[List[float]] = None,
                            y_limits: Optional[List[float]] = None, z_limits: Optional[List[float]] = None,
                            set_ik_limits: bool = True):
    """ Sets rotation constraints on the armature's bone.

    :param bone: The bone to set the constraint to.
    :param x_limits: A list of two float values specifying min/max radiant values along the x-axis or None if no
                     constraint should be applied.
    :param y_limits: A list of two float values specifying min/max radiant values along the y-axis or None if no
                     constraint should be applied.
    :param z_limits: A list of two float values specifying min/max radiant values along the z-axis or None if no
                     constraint should be applied.
    :param set_ik_limits: If true will set inverse kinematics constraints based on the allowed rotation axis.
    """
    if x_limits is None and y_limits is None and z_limits is None:
        return

    # add new constraint if it doesn't exist
    constraint = add_constraint_if_not_existing(bone, constraint_name="Limit Rotation")

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
        set_ik_limits_from_rotation_constraint(bone)


def set_ik_limits_from_rotation_constraint(bone: bpy.types.PoseBone,
                                           constraint: Optional[bpy.types.Constraint] = None):
    """ Sets inverse kinematics limits based on a given rotation constraint.

    :param bone: The bone to set the inverse kinematics limits to.
    :param constraint: The rotation constraint. If None tries to determine it automatically from the bone.
    """
    if constraint is None:
        constraint = get_rotation_constraint(bone=bone)

    if constraint is not None:
        if constraint.use_limit_x:
            if constraint.min_x == constraint.max_x == 0:
                bone.lock_ik_x = True
            else:
                bone.use_ik_limit_x = True
                bone.ik_min_x = constraint.min_x
                bone.ik_max_x = constraint.max_x
        if constraint.use_limit_y:
            if constraint.min_y == constraint.max_y == 0:
                bone.lock_ik_y = True
            else:
                bone.use_ik_limit_y = True
                bone.ik_min_y = constraint.min_y
                bone.ik_max_y = constraint.max_y
        if constraint.use_limit_z:
            if constraint.min_z == constraint.max_z == 0:
                bone.lock_ik_z = True
            else:
                bone.use_ik_limit_z = True
                bone.ik_min_z = constraint.min_z
                bone.ik_max_z = constraint.max_z


def copy_constraints(source_bone: bpy.types.PoseBone, target_bone: bpy.types.PoseBone,
                     constraints_to_be_copied: Optional[List[str]] = None):
    """ Copies constraints from one bone to another.

    :param source_bone: The bone holding the constraints to be copied.
    :param target_bone: The bone where the constraints should be copied to.
    :param constraints_to_be_copied: A list of constraints to copy if not all constraints should be copied.
    """
    for c in source_bone.constraints:
        if constraints_to_be_copied is not None and c.name not in constraints_to_be_copied:
            continue
        c_copy = add_constraint_if_not_existing(target_bone, constraint_name=c.name)
        for prop in dir(c):
            setattr(c_copy, prop, getattr(c, prop))


def set_ik_constraint(bone: bpy.types.PoseBone, target: bpy.types.Armature, target_bone: str, influence: float = 1.,
                      use_rotation: bool = True, chain_length: int = 0):
    """ Sets an inverse kinematics constraint.

    :param bone: The bone to set the constraint to.
    :param target: The armature holding the bone.
    :param target_bone: Name of the target bone which movements shall influence this bone.
    :param influence: Influence of the constraint.
    :param use_rotation: Whether to rotate the child links as well. Defaults to True.
    :param chain_length: The number of parent links which are influenced by this ik bone. Defaults to 0 for all
                         parents.
    """
    c = add_constraint_if_not_existing(bone, constraint_name="IK")
    c.target = target
    c.subtarget = target_bone
    c.influence = influence
    c.use_rotation = use_rotation
    c.chain_count = chain_length


def set_copy_rotation_constraint(bone: bpy.types.PoseBone, target: bpy.types.PoseBone, target_bone: str,
                                 custom_constraint_name: Optional[str] = None, influence: float = 1.):
    """ Sets a copy_rotation constraint.

    :param bone: The bone to set the constraint to.
    :param target: The armature holding the bone.
    :param target_bone: Name of the target bone which rotations shall influence this bone.
    :param custom_constraint_name: Custom name for the constraint. If not specified will use the default name.
    :param influence: Influence of the constraint.
     """
    c = add_constraint_if_not_existing(bone, constraint_name="Copy Rotation",
                                       custom_constraint_name=custom_constraint_name, add_to_existing=True)
    c.target = target
    c.subtarget = target_bone
    c.influence = influence


def set_copy_location_constraint(bone: bpy.types.PoseBone, target: bpy.types.Armature, target_bone: str,
                                 custom_constraint_name: Optional[str] = None, influence: float = 1.,
                                 target_space: str = 'LOCAL', owner_space: str = 'LOCAL'):
    """ Sets a copy_location constraint.

    :param bone: The bone to set the constraint to.
    :param target: The armature holding the bone.
    :param target_bone: Name of the target bone which locations shall influence this bone.
    :param custom_constraint_name: Custom name for the constraint. If not specified will use the default name.
    :param influence: Influence of the constraint.
    :param target_space: Target space of the constraint.
    :param owner_space: Owner space of the constraint.
     """
    c = add_constraint_if_not_existing(bone, constraint_name="Copy Location",
                                       custom_constraint_name=custom_constraint_name, add_to_existing=True)
    c.target = target
    c.subtarget = target_bone
    c.influence = influence
    c.target_space = target_space
    c.owner_space = owner_space


def set_location_constraint(bone: bpy.types.PoseBone, x_limits: Optional[List[float]] = None,
                            y_limits: Optional[List[float]] = None, z_limits: Optional[List[float]] = None):
    """ Sets a location constraint.

    :param bone: The bone to set the constraint to.
    :param x_limits: A list of two float values specifying min/max values along the x-axis or None if no constraint
                     should be applied.
    :param y_limits: A list of two float values specifying min/max values along the y-axis or None if no constraint
                     should be applied.
    :param z_limits: A list of two float values specifying min/max values along the z-axis or None if no constraint
                     should be applied.
    """
    if x_limits is None and y_limits is None and z_limits is None:
        return

    # add new constraint if it doesn't exist
    constraint = add_constraint_if_not_existing(bone, constraint_name="Limit Location")

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


def get_constraint(bone: bpy.types.PoseBone, constraint_name: str = "") -> Optional[bpy.types.Constraint]:
    """ Returns the desired constraint if existing; otherwise None.

    :param bone: The bone to set the constraint to.
    :param constraint_name: Name of the constraint.
    :return: Constraint if it exists; else None.
    """
    if constraint_name in bone.constraints.keys():
        return bone.constraints[constraint_name]
    return None


def get_location_constraint(bone: bpy.types.PoseBone) -> Optional[bpy.types.Constraint]:
    """ Returns the location constraint if existing; otherwise None.

    :param bone: The bone to set the constraint to.
    :return: Location constraint if it exists; else None.
    """
    return get_constraint(bone, constraint_name="Limit Location")


def get_rotation_constraint(bone: bpy.types.PoseBone) -> Optional[bpy.types.Constraint]:
    """ Returns the rotation constraint if existing; otherwise None.

    :param bone: The bone to set the constraint to.
    :return: Rotation constraint if it exists; else None.
    """
    return get_constraint(bone, constraint_name="Limit Rotation")


def remove_constraint(bone: bpy.types.PoseBone, constraint_key: str = ""):
    """ Removes a specified constraint.

    :param bone: The bone to set the constraint to.
    :param constraint_key: Key to be removed.
    """
    bone.constraints.remove(bone.constraints[constraint_key])


def remove_constraints(bone: bpy.types.PoseBone):
    """ Removes all constraints of the armature.

    :param bone: The bone to set the constraint to.
    """
    for constraint_key in bone.constraints.keys():
        remove_constraint(bone=bone, constraint_key=constraint_key)
