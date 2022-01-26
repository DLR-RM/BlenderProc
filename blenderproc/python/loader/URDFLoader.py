from typing import List, Union
import os
from mathutils import Matrix, Vector
import numpy as np

import bpy

from blenderproc.python.utility.SetupUtility import SetupUtility
from blenderproc.python.utility.BlenderUtility import get_all_materials
from blenderproc.python.utility.Utility import Utility
from blenderproc.python.loader.ObjectLoader import load_obj
from blenderproc.python.material import MaterialLoaderUtility
from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.types.MeshObjectUtility import MeshObject, create_primitive
from blenderproc.python.types.URDFUtility import URDFObject, Link, Inertial
from blenderproc.python.filter.Filter import one_by_attr
from blenderproc.python.types.MeshObjectUtility import create_with_empty_mesh
from blenderproc.python.types.BoneUtility import set_location_constraint, set_rotation_constraint, set_copy_rotation_constraint


def load_urdf(urdf_file: str) -> URDFObject:
    """ Loads a urdf object from an URDF file.

    :param urdf_file: Path to the URDF file.
    :return: URDF object instance.
    """
    # install urdfpy
    SetupUtility.setup_pip(user_required_packages=["git+https://github.com/wboerdijk/urdfpy.git"])
    from urdfpy import URDF

    # load urdf tree representation
    urdf_tree = URDF.load(urdf_file)

    # create new empty armature
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.armature_add()
    armature = bpy.context.active_object
    armature.name = urdf_tree.name
    # remove initially created bone
    bpy.ops.object.mode_set(mode='EDIT')
    armature.data.edit_bones.remove(armature.data.edit_bones.values()[0])
    bpy.ops.object.mode_set(mode='OBJECT')

    base_joints = get_joints_which_have_link_as_parent(urdf_tree.base_link.name, urdf_tree.joints)
    import numpy as np
    np.set_printoptions(4, suppress=True)
    for base_joint in base_joints:
        create_bone(armature, base_joint, urdf_tree.joints, parent_bone_name=None, create_recursive=True)

    links = load_links(urdf_tree.links, urdf_tree.joints, armature, urdf_path=urdf_file)

    for base_joint in base_joints:
        propagate_pose(links, base_joint, urdf_tree.joints, armature)

    for link in links:
        link.parent_with_bone(weight_distribution='rigid')

    # set to forward kinematics per default
    for link in links:
        link.switch_fk_ik_mode(mode="fk")

    return URDFObject(armature, links=links, xml_tree=urdf_tree)


def get_joints_which_have_link_as_parent(link_name, joint_trees):
    return [joint_tree for i, joint_tree in enumerate(joint_trees) if joint_tree.parent == link_name]


def get_joints_which_have_link_as_child(link_name, joint_trees):
    valid_joint_trees = [joint_tree for i, joint_tree in enumerate(joint_trees) if joint_tree.child == link_name]
    if valid_joint_trees == []:
        # no joint for link
        print(f"WARNING: There is no joint defined for the link {link_name}!")
        return None
    elif len(valid_joint_trees) == 1:
        return valid_joint_trees[0]
    else:
        raise NotImplementedError(f"More than one ({len(valid_joint_trees)}) joints map onto a single link with name {link_name}")


def create_bone(armature, joint_tree, all_joint_trees, parent_bone_name=None, create_recursive=False,
                parent_origin=None, fk_offset=[0., -1., 0.], ik_offset=[0., 1., 0.]):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    # create initial bone
    edit_bones = armature.data.edit_bones
    editbone = edit_bones.new(joint_tree.name)

    parent_joint = get_joints_which_have_link_as_child(joint_tree.parent, all_joint_trees)
    if parent_joint is not None:
        print("parent joint", parent_joint.name, joint_tree.name)

    origin = joint_tree.origin
    if parent_origin is not None:
        origin = parent_origin @ origin

    axis = Matrix(origin[:3, :3]) @ Vector(joint_tree.axis)
    editbone.head = Vector(origin[:3, -1])
    editbone.tail = editbone.head + axis.normalized() * 0.2

    if parent_bone_name is not None:
        parent_bone = edit_bones.get(parent_bone_name)
        editbone.parent = parent_bone

    # create fk bone
    fk_editbone = edit_bones.new(joint_tree.name + '.fk')
    axis = Matrix(origin[:3, :3]) @ Vector(joint_tree.axis)
    fk_editbone.head = Vector(origin[:3, -1]) + Vector(fk_offset)
    fk_editbone.tail = fk_editbone.head + axis.normalized() * 0.2

    if parent_bone_name is not None:
        parent_bone = edit_bones.get(parent_bone_name + '.fk')
        fk_editbone.parent = parent_bone

    # create ik bone
    ik_editbone = edit_bones.new(joint_tree.name + '.ik')
    axis = Matrix(origin[:3, :3]) @ Vector(joint_tree.axis)
    ik_editbone.head = Vector(origin[:3, -1]) + Vector(ik_offset)
    ik_editbone.tail = ik_editbone.head + axis.normalized() * 0.2

    if parent_bone_name is not None:
        parent_bone = edit_bones.get(parent_bone_name + '.ik')
        ik_editbone.parent = parent_bone

    # this is necessary as after changing to object mode the string will be differently encoded?!
    bone_name = editbone.name
    fk_bone_name = fk_editbone.name
    ik_bone_name = ik_editbone.name

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    # derive posebones for constraints
    bone = armature.pose.bones[bone_name]
    fk_bone = armature.pose.bones[fk_bone_name]
    ik_bone = armature.pose.bones[ik_bone_name]

    # set rotation mode
    bone.rotation_mode = "XYZ"
    fk_bone.rotation_mode = "XYZ"
    ik_bone.rotation_mode = "XYZ"

    # manage constraints
    if joint_tree.joint_type == "fixed":
        set_location_constraint(bone=bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        set_location_constraint(bone=fk_bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        set_location_constraint(bone=ik_bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        set_rotation_constraint(bone=bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        set_rotation_constraint(bone=fk_bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        set_rotation_constraint(bone=ik_bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
    elif joint_tree.joint_type == "revolute":
        limits = None
        if joint_tree.limit is not None:
            limits = np.array([joint_tree.limit.lower, joint_tree.limit.upper])

        set_location_constraint(bone=bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        set_location_constraint(bone=fk_bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        set_location_constraint(bone=ik_bone, x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        set_rotation_constraint(bone=bone, x_limits=[0, 0], y_limits=limits, z_limits=[0, 0])
        set_rotation_constraint(bone=fk_bone, x_limits=[0, 0], y_limits=limits, z_limits=[0, 0])
        set_rotation_constraint(bone=ik_bone, x_limits=[0, 0], y_limits=limits, z_limits=[0, 0])
        set_copy_rotation_constraint(bone=bone, target=armature, target_bone=fk_bone.name,
                                     custom_constraint_name="copy_rotation.fk")
        set_copy_rotation_constraint(bone=bone, target=armature, target_bone=ik_bone.name,
                                     custom_constraint_name="copy_rotation.ik",
                                     influence=0.)  # start in fk mode per default

    else:
        print(f"WARNING: No constraint implemented for joint type '{joint_tree.joint_type}'!")
        # link.bone_name = corresponding_joint.name

    if create_recursive:
        child_joints = get_joints_which_have_link_as_parent(link_name=joint_tree.child, joint_trees=all_joint_trees)

        if child_joints != []:
            for child_joint in child_joints:
                create_bone(armature, child_joint, all_joint_trees, parent_bone_name=bone.name, create_recursive=True,
                            parent_origin=origin, fk_offset=fk_offset)


def load_links(link_trees, joint_trees, armature, urdf_path):
    links = []
    for i, link_tree in enumerate(link_trees):
        inertial, visuals, collisions = None, [], []
        # if link_tree.inertial:
        #    inertial = load_inertial(link_tree.inertial, name=f"{link_tree.name}_inertial")
        if link_tree.visuals:
            visuals = [load_viscol(visual_tree, name=f"{link_tree.name}_visual", urdf_path=urdf_path) for visual_tree in
                       link_tree.visuals]
        # if link_tree.collisions:
        #    collisions = [load_viscol(collision_tree, name=f"{link_tree.name}_collision", urdf_path=urdf_path) for collision_tree in link_tree.collisions]

        # determine bone name
        corresponding_joint = get_joints_which_have_link_as_child(link_tree.name, joint_trees)

        link = Link(bpy_object=create_with_empty_mesh(
            link_tree.name).blender_obj)  # todo is it good to create an empty object to inherit from entity
        link.set_armature(armature)
        link.set_visuals(visuals)
        link.set_collisions(collisions)
        link.set_inertial(inertial)
        link.set_name(name=link_tree.name)

        if corresponding_joint is not None:
            # edit_bones = armature.data.edit_bones
            link.set_bone(armature.pose.bones.get(corresponding_joint.name))
            link.set_fk_bone(armature.pose.bones.get(corresponding_joint.name + '.fk'))
            link.set_ik_bone(armature.pose.bones.get(corresponding_joint.name + '.ik'))
            link.set_joint_type(corresponding_joint.joint_type)

        links.append(link)
    return links


def propagate_pose(links, joint_tree, joint_trees, armature, recursive=True):
    child_link = one_by_attr(elements=links, attr_name="name", value=joint_tree.child)
    parent_link = one_by_attr(elements=links, attr_name="name", value=joint_tree.parent)

    mat = Matrix(parent_link.get_local2world_mat()) @ Matrix(joint_tree.origin)
    child_link.set_local2world_mat(mat)
    child_link.set_parent(parent=parent_link)

    for obj in child_link.get_all_objects():
        obj.set_local2world_mat(Matrix(child_link.get_local2world_mat()) @ Matrix(obj.get_local2world_mat()))

    if recursive:
        child_joint_trees = get_joints_which_have_link_as_parent(child_link.get_name(), joint_trees)
        for child_joint_tree in child_joint_trees:
            propagate_pose(links, child_joint_tree, joint_trees, armature, recursive=True)


def load_geometry(geometry_tree: "urdfpy.Geometry", urdf_path: Union[str, None] = None) -> MeshObject:
    """ Loads a geometric element from a urdf tree.

    :param geometry_tree: The urdf representation of the geometric element.
    :param urdf_path: Optional path of the urdf file for relative geometry files.
    :return: The respective MeshObject.
    """
    if geometry_tree.mesh is not None:
        if os.path.isfile(geometry_tree.mesh.filename):
            obj = load_obj(filepath=geometry_tree.mesh.filename)[0]
        elif urdf_path is not None and os.path.isfile(urdf_path):
            relative_path = os.path.join('/'.join(urdf_path.split('/')[:-1]), geometry_tree.mesh.filename)
            if os.path.isfile(relative_path):
                obj = load_obj(filepath=relative_path, axis_forward='Y', axis_up='Z')[0]  # load in default coordinate system
            else:
                print(f"Couldn't load mesh file for {geometry_tree} (filename: {geometry_tree.mesh.filename}; urdf filename: {urdf_path})")
        else:
            print(f"Couldn't load mesh file for {geometry_tree} (filename: {geometry_tree.mesh.filename})")
    elif geometry_tree.box is not None:
        obj = create_primitive(shape="CUBE")
        obj.blender_obj.dimensions = Vector(geometry_tree.box.size)
    elif geometry_tree.cylinder is not None:
        obj = create_primitive(shape="CYLINDER", radius=geometry_tree.cylinder.radius,
                               depth=geometry_tree.cylinder.length)
    elif geometry_tree.sphere is not None:
        obj = create_primitive(shape="SPHERE", radius=geometry_tree.sphere.radius)
    else:
        raise NotImplementedError(f"Unknown geometry in urdf_tree {geometry_tree}")
    obj.persist_transformation_into_mesh(location=True, rotation=True, scale=True)
    return obj


def load_viscol(viscol_tree: Union["urdfpy.Visual", "urdfpy.Collision"], name: str, urdf_path: Union[str, None] = None) -> MeshObject:
    """ Loads a visual / collision element from an urdf tree.

    :param viscol_tree: The urdf representation of the visual / collision element.
    :param urdf_path: Optional path of the urdf file for relative geometry files.
    :return: The respective MeshObject.
    """
    obj = load_geometry(viscol_tree.geometry, urdf_path=urdf_path)
    try:
        obj.set_name(name=viscol_tree.name)
    except Exception as e:
        # fallback to the link name with specified suffix
        print(f"Didn't find a name for visual / collision object in {viscol_tree} ({e}). Falling back to {name}.")
        obj.set_name(name=name)

    # load material - only valid for visuals
    if hasattr(viscol_tree, "material") and viscol_tree.material is not None:
        # clear all existing materials
        obj.clear_materials()

        # check if material exists
        if viscol_tree.material.name in [m.name for m in get_all_materials()]:
            mat = bpy.data.materials[viscol_tree.material.name]
            mat = Material(mat)
        else:
            # create a new material
            mat = MaterialLoaderUtility.create(name=viscol_tree.material.name)
            # create a principled node and set the default color
            principled_node = mat.get_the_one_node_with_type("BsdfPrincipled")
            color = viscol_tree.material.color
            if color is None:
                color = Vector([1., 1., 1., 1.])
            principled_node.inputs["Base Color"].default_value = color
        obj.replace_materials(mat)

        # check for textures
        if viscol_tree.material.texture is not None:
            # image should've been loaded automatically
            mat = MaterialLoaderUtility.create(name=viscol_tree.material.name + "_texture")
            nodes = mat.nodes
            links = mat.links

            color_image = nodes.new('ShaderNodeTexImage')

            if not os.path.exists(viscol_tree.material.texture.filename):
                raise Exception(f"Couldn't load texture image for {viscol_tree} from {viscol_tree.material.texture.filename}")
            color_image.image = bpy.data.images.load(viscol_tree.material.texture.filename, check_existing=True)

            principled = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")
            links.new(color_image.outputs["Color"], principled.inputs["Base Color"])

            obj.replace_materials(mat)

    # set the pose of the object
    try:
        obj.set_local2world_mat(Matrix(viscol_tree.origin))
        print(f"Set matrix_local of {obj.get_name()} to \n{viscol_tree.origin}")
    except Exception as e:
        print(f"No origin found for {viscol_tree}: {e}. Setting origin to world origin.")
        obj.set_local2world_mat(Matrix.Identity(4))

    # set scale of the mesh
    scale = get_size_from_geometry(viscol_tree.geometry)
    if scale is not None:
        obj.set_scale([scale, scale, scale])
        obj.persist_transformation_into_mesh(location=False, rotation=False, scale=True)

    return obj


def load_inertial(inertial_tree: "urdfpy.Inertial", name: str):
    """ Loads an inertial element from an urdf tree.

    :param inertial_tree: The urdf representation of the inertial element.
    :return: The respective Inertial object.
    """
    # create new primitive
    primitive = create_primitive(shape="CUBE")
    inertial = Inertial(primitive.blender_obj)
    inertial.set_name(name=name)

    # set inertial-specific attributes
    inertial.set_origin(origin=inertial_tree.origin)
    inertial.set_mass(mass=inertial_tree.mass)
    inertial.set_inertia(inertia=inertial_tree.inertia)
    primitive.blender_obj.dimensions = Vector([0.03, 0.03, 0.03])  # just small values to keep cubes small for debugging
    primitive.persist_transformation_into_mesh(location=True, rotation=True, scale=True)
    return inertial


def get_size_from_geometry(geometry: "urdfpy.Geometry") -> float:
    """ Helper to derive the link size from the largest geometric element.

    :param geometry: The urdf representation of the geometric element.
    :return: A single float representing the link's size.
    """
    if geometry.box is not None:
        return max(geometry.geometry.size)
    elif geometry.cylinder is not None:
        return max(geometry.geometry.radius, geometry.geometry.length)
    elif geometry.mesh is not None:
        if hasattr(geometry.geometry, "scale") and geometry.geometry.scale is not None:
            return max(geometry.geometry.scale)
        elif hasattr(geometry.geometry, "size") and geometry.geometry.size is not None:
            return max(geometry.geometry.size)
        return None
    elif geometry.sphere is not None:
        return geometry.geometry.radius
    else:
        print(f"Warning: Failed to derive size from geometry model {geometry}. Setting scale to 0.2!")
        return None
