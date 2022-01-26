import bpy

from typing import Union, List


def get_armature_from_bone(bone_name):
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            if obj.pose.bones.get(bone_name) is not None:
                return obj
    raise NotImplementedError("impossible")


def add_constraint_if_not_existing(bone=None, constraint_name: str = "", custom_constraint_name: str = "",
                                   add_to_existing: bool = False) -> bpy.types.Constraint:
    """ Adds a new constraint.

    :param constraint_name: Name of the desired constraint.
    """
    if custom_constraint_name == "":
        custom_constraint_name = constraint_name
    if constraint_name not in bone.constraints.keys() or add_to_existing:
        c = bone.constraints.new(constraint_name.upper().replace(' ', '_'))
        c.name = custom_constraint_name
        return c
    else:
        return None


def set_rotation_constraint(bone=None, x_limits: Union[List[float], None] = None,
                            y_limits: Union[List[float], None] = None, z_limits: Union[List[float], None] = None,
                            set_ik_limits: bool = True):
    """ Sets rotation constraints on the armature's bone.

    :param x_limits: A list of two float values specifying min/max radiant values along the x-axis or None if no constraint should be applied.
    :param y_limits: A list of two float values specifying min/max radiant values along the y-axis or None if no constraint should be applied.
    :param z_limits: A list of two float values specifying min/max radiant values along the z-axis or None if no constraint should be applied.
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
        set_ik_limits_from_rotation_constraint(bone)  # todo try if necessary


def set_ik_limits_from_rotation_constraint(bone, constraint=None):
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


def copy_constraints(source_bone, target_bone, constraints_to_be_copied=[]):
    # constraints_to_be_copied = [c.upper().replace(' ', '_') for c in constraints_to_be_copied]
    for c in source_bone.constraints:
        print(c.name, constraints_to_be_copied)
        if constraints_to_be_copied != [] and c.name not in constraints_to_be_copied:
            continue
        c_copy = add_constraint_if_not_existing(target_bone, constraint_name=c.name)
        for prop in dir(c):
            try:
                setattr(c_copy, prop, getattr(c, prop))
            except:
                pass


def set_ik_constraint(pose_bone, target, target_bone, influence=1., use_rotation=True):
    c = add_constraint_if_not_existing(pose_bone, constraint_name="IK")
    c.target = target
    c.subtarget = target_bone
    c.influence = influence
    c.use_rotation = use_rotation


def set_copy_rotation_constraint(bone, target, target_bone="", custom_constraint_name="", influence=1.):
    c = add_constraint_if_not_existing(bone, constraint_name="Copy Rotation",
                                       custom_constraint_name=custom_constraint_name, add_to_existing=True)
    c.target = target
    c.subtarget = target_bone
    c.influence = influence


def set_location_constraint(bone=None, x_limits: Union[List[float], None] = None,
                            y_limits: Union[List[float], None] = None, z_limits: Union[List[float], None] = None):
    """ Sets location constraints on the armature's bone.

    :param x_limits: A list of two float values specifying min/max values along the x-axis or None if no constraint should be applied.
    :param y_limits: A list of two float values specifying min/max values along the y-axis or None if no constraint should be applied.
    :param z_limits: A list of two float values specifying min/max values along the z-axis or None if no constraint should be applied.
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


def get_constraint(bone=None, constraint_name: str = "") -> Union[bpy.types.Constraint, None]:
    """ Returns the desired constraint if existing; otherwise None.

    :param constraint_name: Name of the constraint.
    :return: Constraint if it exists; else None.
    """
    if constraint_name in bone.constraints.keys():
        return bone.constraints[constraint_name]
    return None


def get_location_constraint(bone=None) -> Union[bpy.types.Constraint, None]:
    """ Returns the location constraint if existing; otherwise None.

    :return: Location constraint if it exists; else None.
    """
    return get_constraint(bone, constraint_name="Limit Location")


def get_rotation_constraint(bone=None) -> Union[bpy.types.Constraint, None]:
    """ Returns the rotation constraint if existing; otherwise None.

    :return: Rotation constraint if it exists; else None.
    """
    return get_constraint(bone, constraint_name="Limit Rotation")


def remove_constraint(bone=None, constraint_key: str = ""):
    """ Removes a specified constraint.

    :param constraint_key: Key to be removed.
    """
    bone.constraints.remove(bone.constraints[constraint_key])


def remove_constraints(bone=None):
    """ Removes all constraints of the armature. """
    for constraint_key in bone.constraints.keys():
        remove_constraint(bone=bone, constraint_key=constraint_key)
