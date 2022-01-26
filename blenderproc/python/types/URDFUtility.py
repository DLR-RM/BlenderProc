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
from blenderproc.python.types.BoneUtility import get_constraint, set_ik_constraint, set_ik_limits_from_rotation_constraint


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
        object.__setattr__(self, 'ik_bone', None)
        object.__setattr__(self, 'ik_bone_controller', None)
        object.__setattr__(self, 'ik_bone_constraint', None)
        object.__setattr__(self, 'fk_bone', None)
        object.__setattr__(self, 'armature', None)
        object.__setattr__(self, 'fk_ik_mode', "fk")

    def set_parent(self, parent):
        assert isinstance(parent, Link)
        object.__setattr__(self, "parent", parent)

    def get_parent(self):
        return self.parent

    def _set_rotation_euler(self, bone, rotation_euler: Union[float, list, Euler, np.ndarray], mode: str = "absolute",
                            frame: int = 0):
        """ Rotates the armature based on euler angles. Validates values with given constraints.

        :param rotation_euler: The amount of rotation (in radians). Either three floats for x, y and z axes, or a single float.
                               In the latter case, the axis of rotation is derived based on the rotation constraint. If
                               these are not properly set (i.e., two axes must have equal min/max values) an exception will be thrown.
        :param mode: One of ["absolute", "relative"]. For absolute rotations we clip the rotation value based on the constraints.
                     For relative we don't - this will result in inverse motion after the constraint's limits have been reached.
        :param frame: Keyframe where to insert the respective rotations.
        """
        if bone is None:
            bone = self.bone

        assert mode in ["absolute", "relative"]
        if self.fk_ik_mode == "ik":
            self._switch_fk_ik_mode(mode="fk")
        bpy.ops.object.select_all(action='DESELECT')
        # bone = self.blender_obj.pose.bones.get('Bone')

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
                bone.rotation_euler.rotate_axis(axis, rotation_euler)
                print(f"Relatively rotated bone {bone.name} around axis {axis} for {rotation_euler} radians")
            else:
                for axis, rotation in zip(["X", "Y", "Z"], rotation_euler):
                    bone.rotation_euler.rotate_axis(axis, rotation)
                print(f"Relatively rotated {bone.name} for {rotation_euler} radians")

        Utility.insert_keyframe(bone, "rotation_euler", frame)
        if frame > bpy.context.scene.frame_end:
            bpy.context.scene.frame_end += 1

    def set_rotation_euler(self, *args, **kwargs):
        raise NotImplementedError("Please use 'set_rotation_euler_fk()' or set_rotation_euler_ik()'!")

    def set_location(self, *args, **kwargs):
        raise NotImplementedError("Please use 'set_location_ik()'!")

    def set_rotation_euler_fk(self, *args, **kwargs):
        self._set_rotation_euler(bone=self.fk_bone, *args, **kwargs)

    def set_rotation_euler_ik(self, *args, **kwargs):
        self._set_rotation_euler(bone=self.ik_bone_controller, *args, **kwargs)

    #def set_location_fk(self, bone, location):
    #    # location for prismatic joints
    #    raise NotImplementedError()

    #def set_location_ik(self, *args, **kwargs):
    #    self._set_location(bone=self.ik_bone_controller, *args, **kwargs)

    # todo also separate as rotation above?
    # difficult since we also need to switch modes
    def set_location_ik(self, location, frame=0):
        if not isinstance(location, Vector):
            location = Vector(location)
        print("desired location", location)
        assert self.ik_bone_controller is not None, f"No ik bone chain created. Please run 'self.create_ik_bone()' first!"
        if self.fk_ik_mode == "fk":
            print("switching mode")
            self._switch_fk_ik_mode(mode="ik")
        print("desired location", location)

        # first: determine offset to base frame
        self.ik_bone_controller.location = Vector([0., 0., 0.])
        self.ik_bone_controller.rotation_mode = "XYZ"
        self.ik_bone_controller.rotation_euler = Vector([0., 0., 0.])
        bpy.context.view_layer.update()
        offset_mat = self.ik_bone_controller.matrix
        print("offset mat", offset_mat)

        # offset location by ik offset to base bones
        location = location + (self.ik_bone.head - self.bone.head)
        print("loc after offset", location)
        l = Vector([location[0], location[1], location[2], 1.])

        # move to current frame
        location = offset_mat.inverted() @ l
        print("final location", location)
        self.ik_bone_controller.location = location[:3]
        bpy.context.view_layer.update()  # todo necessary with keyframe insert?

        # if frame is not None:  # when changing fk-ik mode the location will also be updated, but this doesn't need to be
        Utility.insert_keyframe(self.ik_bone_controller, "rotation_euler", frame)
        if frame > bpy.context.scene.frame_end:
            bpy.context.scene.frame_end += 1

    def _determine_rotation_axis(self, bone=None):
        """ Determines the single rotation axis and checks if the constraints are set well to have only one axis of freedom.

        :return: The single rotation axis ('X', 'Y' or 'Z').
        """
        c = get_constraint(bone=bone, constraint_name="Limit Rotation")
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

    def set_ik_bone_controller(self, bone):
        object.__setattr__(self, "ik_bone_controller", bone)

    def set_ik_bone_constraint(self, bone):
        object.__setattr__(self, "ik_bone_constraint", bone)

    def set_armature(self, armature):
        object.__setattr__(self, "armature", armature)

    def set_fk_ik_mode(self, mode="fk"):
        object.__setattr__(self, "fk_ik_mode", mode)

    def hide(self, hide_object=True):
        self.hide(hide_object=hide_object)
        for obj in self.get_all_objects():
            obj.hide(hide_object=hide_object)

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

        if self.bone is None:
            # only set parent
            print(f"WARNING: Link {self.get_name()} does not have a bone to be parented with!")
            self.blender_obj.parent = self.armature
            return

        if weight_distribution in ['envelope', 'automatic']:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
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

    def _create_ik_bone_controller(self, relative_location=Vector([0., 0., 0.]), chain_length=0):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode='EDIT')
        self.armature.select_set(True)
        edit_bones = self.armature.data.edit_bones

        # we need two bones: a controll bone and a constraint bone
        # the controll bone will be placed exactly where the current ik bone is
        ik_bone_controller = edit_bones.new(self.ik_bone.name + '.controller')
        ik_bone_controller.head = self.ik_bone.head
        ik_bone_controller.tail = self.ik_bone.tail
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
        set_ik_constraint(self.ik_bone_constraint, self.armature, self.ik_bone_controller.name)
        set_ik_limits_from_rotation_constraint(self.ik_bone_constraint, constraint=self.bone.constraints["Limit Rotation"])

        bpy.ops.object.mode_set(mode='OBJECT')

        return self.ik_bone_constraint, self.ik_bone_controller

    def get_fk_ik_mode(self):
        return self.fk_ik_mode

    def _switch_fk_ik_mode(self, mode="fk", keep_pose=True):
        if self.bone is None:
            return
        assert mode in ["fk", "ik"]
        if mode == "fk":  # turn off copy rotation constraints of fk bone and base bone
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
            self.set_fk_ik_mode(mode="fk")

        else:  # turn off copy rotation constraints of ik bone and base bone
            bpy.context.view_layer.update()

            if keep_pose:
                self.ik_bone.matrix = self.fk_bone.matrix

            if self.joint_type == "revolute":
                self.bone.constraints["copy_rotation.fk"].influence = 0.
                self.bone.constraints["copy_rotation.ik"].influence = 1.

            self.set_fk_ik_mode(mode="ik")
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

            bpy.ops.object.mode_set(mode='OBJECT')


class URDFObject(Entity):
    def __init__(self, armature: bpy.types.Armature, links: List[Link], xml_tree: Union["urdfpy.URDF", None] = None):
        super().__init__(
            bpy_object=armature)  # allows full manipulation (translation, scale, rotation) of whole urdf object
        object.__setattr__(self, "links", links)
        object.__setattr__(self, "xml_tree", xml_tree)
        object.__setattr__(self, "ik_bone_constraint", None)
        object.__setattr__(self, "ik_bone_controller", None)
        object.__setattr__(self, "fk_ik_mode", None)
        object.__setattr__(self, "ik_link", None)

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

        assert len(category_ids) == len(
            self.links), f"Need equal amount of category ids for links. Got {len(category_ids)} and {len(self.links)}, respectively."
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

    def get_all_local2world_mats(self):
        """ Returns all matrix_world matrices from every joint. """

        return np.stack([link.blender_obj.matrix_world for link in self.links])

    def set_ik_bone_controller(self, bone):
        object.__setattr__(self, "ik_bone_controller", bone)

    def set_ik_bone_constraint(self, bone):
        object.__setattr__(self, "ik_bone_constraint", bone)

    def _set_fk_ik_mode(self, mode="fk"):
        object.__setattr__(self, "fk_ik_mode", mode)

    def set_ik_link(self, ik_link):
        object.__setattr__(self, "ik_link", ik_link)

    def create_ik_bone_controller(self, link=None, relative_location=[0., 0., 0.1], chain_length=0):
        if self.ik_bone_controller is not None:
            raise NotImplementedError(
                f"URDFObject already has an ik bone controller. More than one ik controllers are currently not supported!")
        if link is None:
            link = self.links[-1]
        ik_bone_controller, ik_bone_constraint = link._create_ik_bone_controller(relative_location=relative_location,
                                                                                 chain_length=chain_length)
        self.set_ik_bone_controller(ik_bone_controller)
        self.set_ik_bone_constraint(ik_bone_constraint)
        self.set_ik_link(link)
        self.switch_fk_ik_mode(mode="ik")

    def switch_fk_ik_mode(self, mode="fk"):
        if self.fk_ik_mode != mode:
            for link in self.links:
                link._switch_fk_ik_mode(mode=mode)
            self._set_fk_ik_mode(mode=mode)

    def get_revolute_joints(self):
        return [link for link in self.links if link.joint_type == "revolute"]

    def set_rotation_euler(self, *args, **kwargs):
        raise NotImplementedError("Please use 'set_rotation_euler_fk()' or 'set_rotation_euler_ik()'")

    def set_rotation_euler_fk(self, link, rotation_euler, mode, frame=0):
        self.switch_fk_ik_mode(mode="fk")
        if link is not None:
            link.set_rotation_euler_fk(rotation_euler=rotation_euler, mode=mode, frame=frame)
        else:
            revolute_joints = self.get_revolute_joints()
            if len(revolute_joints) == len(rotation_euler):
                for revolute_joint, rotation in zip(revolute_joints, rotation_euler):
                    revolute_joint.set_rotation_euler_fk(rotation_euler=rotation, mode=mode, frame=frame)
            else:
                for revolute_joint in revolute_joints:
                    revolute_joint.set_rotation_euler_fk(rotation_euler=rotation_euler, mode=mode, frame=frame)

    def set_rotation_euler_ik(self, rotation_euler, mode, frame=0):
        self.switch_fk_ik_mode(mode="ik")
        assert self.ik_link is not None
        self.ik_link.set_rotation_euler_ik(rotation_euler=rotation_euler, mode=mode, frame=frame)

    def set_location_ik(self, location, frame=0):
        self.switch_fk_ik_mode(mode="ik")
        assert self.ik_link is not None
        self.ik_link.set_location_ik(location=location, frame=frame)
