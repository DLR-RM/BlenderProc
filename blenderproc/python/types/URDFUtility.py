""" All URDF objects are captured in this class. """

from typing import Union, List, Optional
import numpy as np
from mathutils import Vector, Euler, Matrix

import bpy

from blenderproc.python.utility.Utility import Utility
from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.LinkUtility import Link
from blenderproc.python.types.InertialUtility import Inertial


# as all attributes are accessed via the __getattr__ and __setattr__ in this module, we need to remove the member
# init check
# pylint: disable=no-member
class URDFObject(Entity):
    """
    This class represents an URDF object, which is comprised of an armature and one or multiple links. Among others, it
    serves as an interface for manipulation of the URDF model.
    """
    def __init__(self, armature: bpy.types.Armature, links: List[Link], xml_tree: Optional["urdfpy.URDF"] = None):
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

    def hide_links_and_collision_inertial_objs(self):
        """ Hides links and their respective collision and inertial objects from rendering. """
        self.blender_obj.hide_set(True)
        for link in self.links:
            for obj in link.get_all_objs():
                if "collision" in obj.get_name() or "inertial" in obj.get_name():
                    obj.hide()

    def set_ascending_category_ids(self, category_ids: Optional[List[int]] = None):
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
        child = link_to_be_removed.get_link_child()

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

            grand_child = child.get_link_child()
            while grand_child is not None:
                edit_bones[grand_child.bone.name].head -= offset
                edit_bones[grand_child.bone.name].tail -= offset
                edit_bones[grand_child.fk_bone.name].head -= offset
                edit_bones[grand_child.fk_bone.name].tail -= offset
                edit_bones[grand_child.ik_bone.name].head -= offset
                edit_bones[grand_child.ik_bone.name].tail -= offset
                grand_child = grand_child.get_link_child()

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.update()

            # do the same for the link objects
            for obj in child.get_all_objs():
                obj.set_location(location=obj.get_location() - offset)
            grand_child = child.get_link_child()
            while grand_child is not None:
                for obj in grand_child.get_all_objs():
                    obj.set_location(location=obj.get_location() - offset)
                grand_child = grand_child.get_link_child()

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
        """ Returns all matrix_world matrices from every joint.

        :return: Numpy array of shape (num_bones, 4, 4).
        """

        bpy.context.view_layer.update()
        matrices = []
        for link in self.links:
            if link.bone is not None:
                matrices.append(Matrix(self.get_local2world_mat()) @ link.bone.matrix)
        return np.stack(matrices)

    def get_all_visual_local2world_mats(self) -> np.array:
        """ Returns all transformations from world frame to the visual objects.

        :return: Numpy array of shape (num_bones, 4, 4).
        """
        return np.stack([link.get_visual_local2world_mats(Matrix(self.get_local2world_mat())) for link in self.links])

    def get_all_collision_local2world_mats(self) -> np.array:
        """ Returns all transformations from the world frame to the collision objects.

        :return: Numpy array of shape (num_bones, 4, 4).
        """
        return np.stack([
            link.get_collision_local2world_mats(Matrix(self.get_local2world_mat())) for link in self.links
        ])

    def get_all_inertial_local2world_mats(self) -> np.array:
        """ Returns all transformations from the world frame to the inertial objects.

        :return: Numpy array of shape (num_bones, 4, 4).
        """
        return np.stack([link.get_inertial_local2world_mat(Matrix(self.get_local2world_mat())) for link in self.links])

    def _set_ik_bone_controller(self, bone: bpy.types.PoseBone):
        """ Sets the ik bone controller.

        :param bone: Bone to set as ik control bone.
        """
        object.__setattr__(self, "ik_bone_controller", bone)

    def _set_ik_bone_constraint(self, bone: bpy.types.PoseBone):
        """ Sets the ik bone constraint.

        :param bone: Bone to set as ik constraint bone.
        """
        object.__setattr__(self, "ik_bone_constraint", bone)

    def _set_fk_ik_mode(self, mode: str = "fk"):
        """ Sets the mode of the bone chain.

        :param mode: One of "fk" or "ik" for forward / inverse kinematic.
        """
        object.__setattr__(self, "fk_ik_mode", mode)

    def _set_ik_link(self, ik_link: Optional[Link]):
        """ Sets the ik link constraint.

        :param ik_link: Link to set as ik link.
        """
        object.__setattr__(self, "ik_link", ik_link)

    def create_ik_bone_controller(self, link: Optional[Link] = None,
                                  relative_location: Optional[Union[List[float], Vector]] = None,
                                  use_rotation: bool = True,
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
        if relative_location is None:
            relative_location = [0., 0., 0.]
        if link is None:
            link = self.links[-1]
        ik_bone_controller, ik_bone_constraint, offset = link.create_ik_bone_controller(
            relative_location=relative_location, use_rotation=use_rotation, chain_length=chain_length)
        self._set_ik_bone_controller(ik_bone_controller)
        self._set_ik_bone_constraint(ik_bone_constraint)
        self._set_ik_bone_offset(offset=offset)
        self._set_ik_link(link)
        self._switch_fk_ik_mode(mode="ik")

    def _switch_fk_ik_mode(self, mode: str = "fk", keep_pose: bool = True):
        """ Switches between forward and inverse kinematics mode. Will do this automatically when switching between e.g.
            `set_rotation_euler_fk()` and `set_rotation_euler_ik()`.

        :param mode: One of  for forward / inverse kinematik.
        :param keep_pose: If specified, will keep the pose when switching modes. Otherwise, will return to the old pose
                          of the previously selected mode.
        """
        if mode == "ik" and self.ik_bone_controller is None:
            raise NotImplementedError("URDFObject doesn't have an ik bone controller. Please set up an ik bone first "
                                      "with 'urdf_object.create_ik_bone_controller()'")
        if self.fk_ik_mode != mode:
            for link in self.links:
                link.switch_fk_ik_mode(mode=mode, keep_pose=keep_pose)
            self._set_fk_ik_mode(mode=mode)

    def get_links_with_revolute_joints(self) -> List[Link]:
        """ Returns all revolute joints.

        :return: List of revolute joints.
        """
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

    def set_rotation_euler_fk(self, link: Optional[Link], rotation_euler: Union[float, List[float], Euler, np.ndarray],
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
            revolute_joints = self.get_links_with_revolute_joints()
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
        print(f'Pose is not within given constraints:\n'
              f'  translation difference: {t_diff:.4f} (max: {location_error})\n'
              f'  rotation difference: {q_diff:.4f} (max: {rotation_error})')
        return False

    def _set_ik_bone_offset(self, offset: Matrix):
        """ Sets the location offset between the control and constraint bone.

        :param offset: The location offset.
        """
        object.__setattr__(self, "ik_bone_offset", offset)

# pylint: enable=no-member
