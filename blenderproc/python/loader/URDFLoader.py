from typing import List, Union
import os
import urdfpy
from mathutils import Matrix, Vector
from urdfpy import URDF

import bpy

from blenderproc.python.utility.BlenderUtility import get_all_materials
from blenderproc.python.utility.Utility import Utility
from blenderproc.python.loader.ObjectLoader import load_obj
from blenderproc.python.material import MaterialLoaderUtility
from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.types.MeshObjectUtility import MeshObject, create_primitive
from blenderproc.python.types.URDFUtility import URDFObject, Link, Inertial


def load_urdf(urdf_file: str) -> URDFObject:
    """ Loads a urdf object from an URDF file.

    :param urdf_file: Path to the URDF file.
    :return: URDF object instance.
    """
    # load urdf tree representation
    urdf_tree = URDF.load(urdf_file)

    # create links
    links = load_links(urdf_tree.links)

    # recursively assign transformations depending on the local joint poses
    for i, joint_tree in enumerate(urdf_tree.joints):
        child = links[i + 1]
        parent = links[i]

        # convenient insanity check
        assert child.get_name() == joint_tree.child
        assert parent.get_name() == joint_tree.parent

        # we also add some information to the link
        child.set_joint_type(joint_type=joint_tree.joint_type)

        # traverse local poses
        child.blender_obj.matrix_world = parent.blender_obj.matrix_world @ Matrix(joint_tree.origin)
        for obj in child.get_children():
            obj.blender_obj.matrix_local = child.blender_obj.matrix_world @ obj.blender_obj.matrix_world

        # we also rotate the armature so that we rotate always around the y axis
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = child.blender_obj
        child.select()
        bpy.ops.object.mode_set(mode='EDIT')
        editbone = child.blender_obj.data.edit_bones["Bone"]
        length = editbone.length
        axis = Vector(joint_tree.axis)
        editbone.tail = editbone.head + axis.normalized() * length
        bpy.ops.object.mode_set(mode='OBJECT')

        # last but not least, we apply constraints
        if joint_tree.joint_type == "fixed":
            child.set_location_constraint(x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
            child.set_rotation_constraint(x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
        elif joint_tree.joint_type == "revolute":
            child.set_location_constraint(x_limits=[0., 0.], y_limits=[0., 0.], z_limits=[0., 0.])
            child.set_rotation_constraint(x_limits=[0., 0.], y_limits=[joint_tree.limit.lower, joint_tree.limit.upper], z_limits=[0., 0.])
        else:
            print(f"WARNING: No constraint implemented for joint type '{joint_tree.joint_type}'!")

    # parent links with their children
    for i, link in enumerate(links):
        bpy.ops.object.select_all(action='DESELECT')
        link.select()
        if i != len(links) - 1:  # select the next link
            links[i + 1].select()

        # select all visuals, collisions and inertial objects
        for obj in link.get_children():
            obj.select()

        # select which object to parent to
        bpy.context.view_layer.objects.active = link.blender_obj

        # parent object
        bpy.ops.object.posemode_toggle()
        bpy.ops.object.parent_set(type="BONE")
        bpy.ops.object.posemode_toggle()

    # check that the first link is actually the base link, this is just an insanity check
    assert links[0].get_name() == urdf_tree.base_link.name

    return URDFObject(name=urdf_tree.name, links=links, other_xml=urdf_tree.other_xml)


def load_links(link_trees: List[urdfpy.Link]) -> List[Link]:
    """ Loads links given a list of urdfpy.Link representations.

    :param link_trees: List of urdf representations of the links.
    :return: List of links.
    """
    if not isinstance(link_trees, list):
        link_trees = list(link_trees)
    links = []
    for i, link_tree in enumerate(link_trees):
        # create armature/bone
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.armature_add()
        link = Link(bpy_object=bpy.context.active_object)

        # give a name to the link
        if link_tree.name is not None:
            link.set_name(name=link_tree.name)
            print(f"Initialized link {link.get_name()}")
        else:
            link.set_name(name=f"link_{i}")
            print(f"No link name defined for {link_tree}. Set name to link list index: {link.get_name()}")

        # set size
        if link_tree.visuals or link_tree.collisions:
            scale = max(get_size_from_geometry(viscol.geometry) for viscol in link_tree.visuals + link_tree.collisions)
        else:
            scale = 0.2
        link.set_scale(scale=[scale, scale, scale])
        print(f"Set scale of {link.get_name()} to {scale}")
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=False)

        # create inertial
        if link_tree.inertial:
            link.set_inertial(load_inertial(link_tree.inertial, name=f"{link.get_name()}_inertial"))

        # create geometric elements
        if link_tree.visuals:
            link.set_visuals([load_viscol(visual_tree, name=f"{link.get_name()}_visual") for visual_tree in link_tree.visuals])
        if link_tree.collisions:
            link.set_collisions([load_viscol(collision_tree, name=f"{link.get_name()}_collision") for collision_tree in link_tree.collisions])

        links.append(link)
    return links


def load_geometry(geometry_tree: urdfpy.Geometry) -> MeshObject:
    """ Loads a geometric element from a urdf tree.

    :param geometry_tree: The urdf representation of the geometric element.
    :return: The respective MeshObject.
    """
    if geometry_tree.mesh is not None:
        if not os.path.isfile(geometry_tree.mesh.filename):
            print(f"Couldn't load mesh file for {geometry_tree} (filename: {geometry_tree.mesh.filename})")
        else:
            obj = load_obj(filepath=geometry_tree.mesh.filename)[0]
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
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=True)
    return obj


def load_viscol(viscol_tree: Union[urdfpy.Visual, urdfpy.Collision], name: str) -> MeshObject:
    """ Loads a visual / collision element from an urdf tree.

    :param viscol_tree: The urdf representation of the visual / collision element.
    :return: The respective MeshObject.
    """
    obj = load_geometry(viscol_tree.geometry)
    try:
        obj.set_name(name=viscol_tree.name)
    except Exception as e:
        # fallback to the link name with specified suffix
        print(f"Didn't find a name for visual / collision object in {viscol_tree} ({e}). Falling back to {name}.")
        obj.set_name(name=name)

    # load material - only valid for visuals
    if hasattr(viscol_tree, "material"):
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
            principled_node.inputs["Base Color"].default_value = viscol_tree.material.color
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

            if obj.blender_obj.data.materials:
                # assign to 1st material slot
                obj.blender_obj.data.materials[0] = mat
            else:
                # no slots
                obj.blender_obj.data.materials.append(mat)

    # set the pose of the object
    try:
        obj.blender_obj.matrix_world = Matrix(viscol_tree.origin)
        print(f"Set matrix_local of {obj.get_name()} to \n{viscol_tree.origin}")
    except Exception as e:
        print(f"No origin found for {viscol_tree}: {e}. Setting origin to world origin.")
        obj.blender_obj.matrix_world = Matrix.Identity(4)

    return obj


def load_inertial(inertial_tree: urdfpy.Inertial, name: str):
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
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, properties=True)

    return inertial


def get_size_from_geometry(geometry: urdfpy.Geometry) -> float:
    """ Helper to derive the link size from the largest geometric element.

    :param geometry: The urdf representation of the geometric element.
    :return: A single float representing the link's size.
    """
    if geometry.box is not None:
        return max(geometry.geometry.size)
    elif geometry.cylinder is not None:
        return max(geometry.geometry.radius, geometry.geometry.length)
    elif geometry.mesh is not None:
        return max(geometry.geometry.size) if hasattr(geometry.geometry, "size") else 0.2
    elif geometry.sphere is not None:
        return geometry.geometry.radius
    else:
        print(f"Warning: Failed to derive size from geometry model {geometry}. Setting scale to 0.2!")
        return 0.2
