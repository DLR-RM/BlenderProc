import bpy
import bmesh
import mathutils
from mathutils import Vector
from sys import platform

import numpy as np
import imageio


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


def get_all_mesh_objects():
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
        if platform == "darwin":
            error = "On Mac OS you manually need to install the imageio .exr extension. This is quite simple: \n"
            error += "Use a different python environment (not blenders internal environment), `pip install imageio`.\n"
            error += 'And then execute the following command in this env: \n'
            error += '`python -c "import imageio; imageio.plugins.freeimage.download()"`\n'
            error += "Now everything should work -> run the pipeline again."
            raise Exception(error)
        raise e


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
