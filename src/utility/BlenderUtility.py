from collections import defaultdict

import bpy
import bmesh
import mathutils
from mathutils import Vector
from sys import platform

import numpy as np
import imageio

from src.utility.Utility import Utility


def local_to_world(cords, world):
    """
    Returns a cords transformed to the given transformation world matrix

    :param cords: coordinates a tuple of 3 values for x,y,z
    :param world: world matrix <- transformation matrix
    """
    return [world @ Vector(cord) for cord in cords]


def get_bounds(obj):
    """
    :param obj: a mesh object
    :return: [8x[3xfloat]] the object aligned bounding box coordinates in world coordinates
    """
    return local_to_world(obj.bound_box, obj.matrix_world)


def check_bb_intersection(obj1, obj2):
    """
    Checks if there is a bounding box collision, these don't have to be axis-aligned, but if they are not:
    The surrounding/including axis-aligned bounding box is calculated and used to check the intersection.

    :param obj1: object 1  to check for intersection, must be a mesh
    :param obj2: object 2  to check for intersection, must be a mesh
    :return: True if the two bounding boxes intersect with each other
    """
    b1w = get_bounds(obj1)

    def min_and_max_point(bb):
        """
        Find the minimum and maximum point of the bounding box
        :param bb: bounding box
        :return: min, max
        """
        values = np.array(bb)
        return np.min(values, axis=0), np.max(values, axis=0)

    # get min and max point of the axis-aligned bounding box
    min_b1, max_b1 = min_and_max_point(b1w)
    b2w = get_bounds(obj2)
    # get min and max point of the axis-aligned bounding box
    min_b2, max_b2 = min_and_max_point(b2w)
    return check_bb_intersection_on_values(min_b1, max_b1, min_b2, max_b2)


def check_bb_intersection_on_values(min_b1, max_b1, min_b2, max_b2, used_check=lambda a, b: a >= b):
    """
    Checks if there is an intersection of the given bounding box values. Here we use two different bounding boxes,
    namely b1 and b2. Each of them has a corresponding set of min and max values, this works for 2 and 3 dimensional
    problems.

    :param min_b1: List of minimum bounding box points for b1.
    :param max_b1: List of maximum bounding box points for b1.
    :param min_b2: List of minimum bounding box points for b2.
    :param max_b2: List of maximum bounding box points for b2.
    :param used_check: The operation used inside of the is_overlapping1D. With that it possible to change the \
                       collision check from volume and surface check to pure surface or volume checks.
    :return: True if the two bounding boxes intersect with each other
    """
    collide = True
    for min_b1_val, max_b1_val, min_b2_val, max_b2_val in zip(min_b1, max_b1, min_b2, max_b2):
        # inspired by this:
        # https://stackoverflow.com/questions/20925818/algorithm-to-check-if-two-boxes-overlap
        # Checks in each dimension, if there is an overlap if this happens it must be an overlap in 3D, too.
        def is_overlapping_1D(x_min_1, x_max_1, x_min_2, x_max_2):
            # returns true if the min and max values are overlapping
            return used_check(x_max_1, x_min_2) and used_check(x_max_2, x_min_1)

        collide = collide and is_overlapping_1D(min_b1_val, max_b1_val, min_b2_val, max_b2_val)
    return collide


def check_intersection(obj1, obj2, skip_inside_check=False, bvh_cache=None):
    """
    Checks if the two objects are intersecting.

    This will use BVH trees to check whether the objects are overlapping.

    It is further also checked if one object is completely inside the other.
    This check requires that both objects are watertight, have correct normals and are coherent.
    If this is not the case it can be disabled via the parameter skip_inside_check.

    :param obj1: object 1 to check for intersection, must be a mesh
    :param obj2: object 2 to check for intersection, must be a mesh
    :param skip_inside_check: Disables checking whether one object is completely inside the other.
    :return: True, if they are intersecting
    """

    if bvh_cache is None:
        bvh_cache = {}

    # If one of the objects has no vertices, collision is impossible
    if len(obj1.data.vertices) == 0 or len(obj2.data.vertices) == 0:
        return False, bvh_cache

    # create bvhtree for obj1
    if obj1.name not in bvh_cache:
        obj1_BVHtree = create_bvh_tree_for_object(obj1)
        bvh_cache[obj1.name] = obj1_BVHtree
    else:
        obj1_BVHtree = bvh_cache[obj1.name]

    # create bvhtree for obj2
    if obj2.name not in bvh_cache:
        obj2_BVHtree = create_bvh_tree_for_object(obj2)
        bvh_cache[obj2.name] = obj2_BVHtree
    else:
        obj2_BVHtree = bvh_cache[obj2.name]

    # Check whether both meshes intersect
    inter = len(obj1_BVHtree.overlap(obj2_BVHtree)) > 0

    # Optionally check whether obj2 is contained in obj1
    if not inter and not skip_inside_check:
        inter = is_point_inside_object(obj1, obj1_BVHtree, obj2.matrix_world @ obj2.data.vertices[0].co)
        print("Warning: Detected that " + obj2.name + " is completely inside " + obj1.name +
              ". This might be wrong, if " + obj1.name +
              " is not water tight or has incorrect normals. If that is the case, consider setting "
              "skip_inside_check to True.")

    # Optionally check whether obj1 is contained in obj2
    if not inter and not skip_inside_check:
        inter = is_point_inside_object(obj2, obj2_BVHtree, obj1.matrix_world @ obj1.data.vertices[0].co)
        print("Warning: Detected that " + obj1.name + " is completely inside " + obj2.name +
              ". This might be wrong, if " + obj2.name + " is not water tight or has incorrect "
                                                         "normals. If that is the case, consider "
                                                         "setting skip_inside_check to True.")

    return inter, bvh_cache


def create_bvh_tree_for_object(obj):
    """ Creates a fresh BVH tree for the given object

    :param obj: The object
    :return: The BVH tree
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    obj_BVHtree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
    return obj_BVHtree


def is_point_inside_object(obj, obj_BVHtree, point):
    """ Checks whether the given point is inside the given object.

    This only works if the given object is watertight and has correct normals

    :param obj: The object
    :param obj_BVHtree: A bvh tree of the object
    :param point: The point to check
    :return: True, if the point is inside the object
    """
    # Look for closest point on object
    nearest, normal, _, _ = obj_BVHtree.find_nearest(point)
    # Compute direction
    p2 = nearest - point
    # Compute dot product between direction and normal vector
    a = p2.normalized().dot((obj.rotation_euler.to_matrix() @ normal).normalized())
    return a >= 0.0


def check_if_uv_coordinates_are_set(obj: bpy.types.Object):
    """
    :param obj: should be an object, which has a mesh
    """
    if len(obj.data.uv_layers) > 1:
        raise Exception("This only support objects which only have one uv layer.")
    for layer in obj.data.uv_layers:
        max_val = np.max([list(uv_coords.uv) for uv_coords in layer.data])
        return max_val > 1e-7
    return False


def vector_to_euler(vector, vector_type):
    """
    :param vector: UP (for MESH objs) of FORWARD (for LIGHT/CAMERA objs) vector. Type: mathutils.Vector.
    :param vector_type: Type of an input vector: UP or FORWARD. Type: string.
    :return: Corresponding Euler angles XYZ-triplet. Type: mathutils Euler.
    """
    # Check vector type
    if vector_type == "UP":
        # UP vectors are used for MESH type objects
        euler_angles = vector.to_track_quat('Z', 'Y').to_euler()
    elif vector_type == "FORWARD":
        # FORWARD vectors are used for LIGHT and CAMERA type objects
        euler_angles = vector.to_track_quat('-Z', 'Y').to_euler()
    else:
        raise Exception("Unknown vector type: " + vector_type)

    return euler_angles


def add_object_only_with_vertices(vertices, name='NewVertexObject'):
    """
    Generates a new object with the given vertices, no edges or faces are generated.

    :param vertices: [[float, float, float]] list of vertices
    :param name: str name of the new object
    :return: the generated obj
    """
    mesh = bpy.data.meshes.new('mesh')
    # create new object
    obj = bpy.data.objects.new(name, mesh)
    # TODO check if this always works?
    col = bpy.data.collections.get('Collection')
    # link object in collection
    col.objects.link(obj)

    # convert vertices to mesh
    bm = bmesh.new()
    for v in vertices:
        bm.verts.new(v)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def add_object_only_with_direction_vectors(vertices, normals, radius=1.0, name='NewDirectionObject'):
    """
    Generates a new object with the given vertices, no edges or faces are generated.

    :param vertices: [[float, float, float]] list of vertices
    :param name: str name of the new object
    :return: the generated obj
    """
    if len(vertices) != len(normals):
        raise Exception("The lenght of the vertices and normals is not equal!")

    mesh = bpy.data.meshes.new('mesh')
    # create new object
    obj = bpy.data.objects.new(name, mesh)
    # TODO check if this always works?
    col = bpy.data.collections.get('Collection')
    # link object in collection
    col.objects.link(obj)

    # convert vertices to mesh
    bm = bmesh.new()
    for v, n in zip(vertices, normals):
        v1 = bm.verts.new(v)
        new_vert = v + n * radius
        v2 = bm.verts.new(new_vert)
        bm.edges.new([v1, v2])
    bm.to_mesh(mesh)
    bm.free()
    return obj


def add_cube_based_on_bb(bouding_box, name='NewCube'):
    """
    Generates a cube based on the given bounding box, the bounding_box can be generated with our get_bounds(obj) fct.

    :param bounding_box: bound_box [8x[3xfloat]], with 8 vertices for each corner
    :param name: name of the new cube
    :return: the generated object
    """
    if len(bouding_box) != 8:
        raise Exception("The amount of vertices is wrong for this bounding box!")
    mesh = bpy.data.meshes.new('mesh')
    # create new object
    obj = bpy.data.objects.new(name, mesh)
    # TODO check if this always works?
    col = bpy.data.collections.get('Collection')
    # link object in collection
    col.objects.link(obj)

    # convert vertices to mesh
    new_vertices = []
    bm = bmesh.new()
    for v in bouding_box:
        new_vertices.append(bm.verts.new(v))
    # create all 6 surfaces, the ordering is depending on the ordering of the vertices in the bounding box
    bm.faces.new([new_vertices[0], new_vertices[1], new_vertices[2], new_vertices[3]])
    bm.faces.new([new_vertices[0], new_vertices[4], new_vertices[5], new_vertices[1]])
    bm.faces.new([new_vertices[1], new_vertices[5], new_vertices[6], new_vertices[2]])
    bm.faces.new([new_vertices[2], new_vertices[3], new_vertices[7], new_vertices[6]])
    bm.faces.new([new_vertices[0], new_vertices[4], new_vertices[7], new_vertices[3]])
    bm.faces.new([new_vertices[4], new_vertices[5], new_vertices[6], new_vertices[7]])
    bm.to_mesh(mesh)
    bm.free()
    return obj


def get_all_blender_mesh_objects() -> list:
    """
    Returns a list of all mesh objects in the scene
    :return: a list of all mesh objects
    """
    return [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']


def get_all_materials():
    """
    Returns a list of all materials used and unused
    :return: a list of all materials
    """
    return list(bpy.data.materials)


def get_all_textures():
    """
    Returns a list of all textures.
    :return: All textures. Type: list.
    """
    return list(bpy.data.textures)


def load_image(file_path, num_channels=3):
    """ Load the image at the given path returns its pixels as a numpy array.

    The alpha channel is neglected.

    :param file_path: The path to the image.
    :param num_channels: Number of channels to return.
    :return: The numpy array
    """
    try:
        return imageio.imread(file_path)[:, :, :num_channels]
    except ValueError as e:
        print("It seems the freeimage library which is necessary to read .exr files cannot be found on your computer.")
        print("Gonna try to download it automatically.")

        # Since PEP 476 the certificate of https connections is verified per default.
        # However, in the blender python env no local certificates seem to be found which makes certification impossible.
        # Therefore, we have to switch certificate verification off for now.
        import ssl
        if hasattr(ssl, '_create_unverified_context'):
            prev_context = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context

        # Download free image library
        imageio.plugins.freeimage.download()

        # Undo certificate check changes
        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = prev_context

        try:
            # Try again
            return imageio.imread(file_path)[:, :, :num_channels]
        except ValueError as e:
            error = "The automatic installation of the freeimage library failed, so you need to install the imageio .exr extension manually. This is quite simple: \n"
            error += "Use a different python environment (not blenders internal environment), `pip install imageio`.\n"
            error += 'And then execute the following command in this env: \n'
            error += '`python -c "import imageio; imageio.plugins.freeimage.download()"`\n'
            error += "Now everything should work -> run the pipeline again."
            raise Exception(error)


def get_bound_volume(obj):
    """ Gets the volume of a possible orientated bounding box.
    :param obj: Mesh object.
    :return: volume of a bounding box.
    """
    bb = get_bounds(obj)
    # Search for the point which is the maximum distance away from the first point
    # we call this first point min and the furthest away point max
    # the vector between the two is a diagonal of the bounding box
    min_point, max_point = bb[0], None
    max_dist = -1
    for point in bb:
        dist = (point - min_point).length
        if dist > max_dist:
            max_point = point
            max_dist = dist
    diag = max_point - min_point
    # use the diagonal to calculate the volume of the box
    return abs(diag[0]) * abs(diag[1]) * abs(diag[2])


def duplicate_objects(objects):
    """
    Creates duplicates of objects, first duplicates are given name <orignial_object_name>.001

    :param objects: an object or a list of objects to be duplicated
    :return: a list of objects
    """
    if not isinstance(objects, list):
        objects = [objects]

    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.object.duplicate()
    duplicates = bpy.context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')
    return duplicates


def collect_all_orphan_datablocks():
    """ Returns all orphan data blocks grouped by their type

    :return: A dict of sets
    """
    orphans = defaultdict(set)
    # Go over all datablock types
    for collection_name in dir(bpy.data):
        collection = getattr(bpy.data, collection_name)
        if isinstance(collection, bpy.types.bpy_prop_collection):
            # Go over all datablocks of that type
            for datablock in collection:
                # Add them to the list if they are orphan
                if datablock.users == 0:
                    orphans[collection_name].add(datablock)

    return orphans


def copy_attributes(attributes: list, old_prop: str, new_prop: str):
    """
    Copies the list of attributes from the old to the new prop if the attribute exists.

    :param: attributes: Current selected attributes
    :param: old_prop: Old property
    :param: new_prop: New property
    """

    # check if the attribute exists and copy it
    for attr in attributes:
        if hasattr(new_prop, attr):
            setattr(new_prop, attr, getattr(old_prop, attr))


def get_node_attributes(node: bpy.types.Node) -> list:
    """
    Returns a list of all properties identifiers if they should not be ignored

    :param: node: the node which attributes should be returned
    :return list of attributes of the given node
    """

    # all attributes that shouldn't be copied
    ignore_attributes = ("rna_type", "type", "dimensions", "inputs", "outputs", "internal_links", "select",
                         "texture_mapping", "color_mapping", "image_user", "interface")

    attributes = []
    for attr in node.bl_rna.properties:
        #check if the attribute should be copied and add it to the list of attributes to copy
        if not attr.identifier in ignore_attributes and not attr.identifier.split("_")[0] == "bl":
            attributes.append(attr.identifier)

    return attributes


def copy_nodes(nodes: bpy.types.Nodes, goal_nodes: bpy.types.Nodes):
    """
    Copies all nodes from the given list into the group with their attributes

    :param: node: the nodes which should be copied
    :param: goal_nodes: the nodes where they should be copied too
    """

    if len(goal_nodes) > 0:
        raise Exception(f"This function only works if goal_nodes was empty before, has {len(goal_nodes)} elements.")

    # the attributes that should be copied for every link
    input_attributes = ["default_value", "name"]
    output_attributes = ["default_value", "name"]

    for node in nodes:
        # create a new node in the goal_nodes and find and copy its attributes
        new_node = goal_nodes.new(node.bl_idname)
        node_attributes = get_node_attributes(node)
        copy_attributes(node_attributes, node, new_node)

        # copy the attributes for all inputs
        for inp, new_inp in zip(node.inputs, new_node.inputs):
            copy_attributes(input_attributes, inp, new_inp)

        # copy the attributes for all outputs
        for out, new_out in zip(node.outputs, new_node.outputs):
            copy_attributes(output_attributes, out, new_out)


def copy_links(nodes: bpy.types.Nodes, goal_nodes: bpy.types.Nodes, goal_links: bpy.types.NodeLinks):
    """
    Copies all links between the nodes to goal_links with the goal_nodes.

    :param nodes: Nodes, which are used as base for the copying
    :param goal_nodes: Nodes, which are will be newly connected
    :param goal_links: Links, where all the newly generated links are saved
    """

    for node in nodes:
        # find the corresponding node
        new_node = goal_nodes[node.name]

        # enumerate over every link in the nodes inputs
        for i, inp in enumerate(node.inputs):
            for link in inp.links:
                # find the connected node for the link
                connected_node = goal_nodes[link.from_node.name]
                # connect the goal nodes
                goal_links.new(connected_node.outputs[link.from_socket.name], new_node.inputs[i])


def add_group_nodes(group: bpy.types.ShaderNodeTree):
    """
    Adds the group input and output node and positions them correctly.

    :param group: the group which will get an output and input node
    :return bpy.types.NodeGroupInput, bpy.types.NodeGroupOutput: the input and output to the given group
    """

    # add group input and output
    group_input = group.nodes.new("NodeGroupInput")
    group_output = group.nodes.new("NodeGroupOutput")

    # if there are any nodes in the group, find the min and maxi x position of all nodes and position the group nodes
    if len(group.nodes) > 0:
        min_pos = 9999999
        max_pos = -9999999

        for node in group.nodes:
            if node.location[0] < min_pos:
                min_pos = node.location[0]
            elif node.location[0] + node.width > max_pos:
                max_pos = node.location[0]

        group_input.location = (min_pos - 250, 0)
        group_output.location = (max_pos + 250, 0)
    return group_input, group_output


def copy_nodes_from_mat_to_material(from_material: bpy.types.Material, to_material: bpy.types.Material):
    """
    Copy nodes from one material to another material

    :param from_material: The material from which the nodes are selected
    :param to_material: The material to which the nodes will be copied
    """
    # get the list of all selected nodes from the active objects active material
    nodes = from_material.node_tree.nodes

    # copy all nodes from from_material to the to_material with all their attributes
    copy_nodes(nodes, to_material.node_tree.nodes)

    # copy the links between the nodes to the to_material
    copy_links(nodes, to_material.node_tree.nodes, to_material.node_tree.links)


def add_nodes_to_group(nodes: bpy.types.Node, group_name: str) -> bpy.types.ShaderNodeTree:
    """
    Creates the node group, copies all attributes and links and adds the group input and output
    https://blender.stackexchange.com/a/175604

    :param nodes: Nodes, which should be used
    :param group_name: Name of the group
    :return bpy.types.ShaderNodeTree: the group which can be used inside of a bpy.types.ShaderNodeGroup
    """
    # create new node group
    group = bpy.data.node_groups.new(name=group_name, type="ShaderNodeTree")

    # copy all nodes from the list to the created group with all their attributes
    copy_nodes(nodes, group.nodes)

    # copy the links between the nodes to the created groups nodes
    copy_links(nodes, group.nodes, group.links)

    # add the group input and output node to the created group
    group_input, group_output = add_group_nodes(group)

    # check if the selection of nodes goes over a material, if so replace the material output with the output of
    # the group
    material_outputs = Utility.get_nodes_with_type(group.nodes, "OutputMaterial")
    if len(material_outputs) == 1:
        for input in material_outputs[0].inputs:
            group.outputs.new(input.bl_idname, input.name)
            for link in input.links:
                group.links.new(link.from_socket, group_output.inputs[input.name])
        # remove the material output, the material output should never be inside of a group
        group.nodes.remove(material_outputs[0])
    return group
