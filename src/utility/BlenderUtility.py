import bpy
import bmesh
from mathutils import Vector

import numpy as np


def triangulate(obj, transform=True, triangulate=True, apply_modifiers=False):
    """
    :obj: object to triangulate, must be a mesh
    :transform: transform to world coordinates if True
    :triangulate: perform triangulation if True
    :apply_modifiers: applies modifiers if any and True
    Returns a transformed, triangulated copy of the mesh (much smaller in size and can be used for quicker maths)
    """
    assert(obj.type == 'MESH')

    if apply_modifiers and obj.modifiers:
        me = obj.to_mesh(bpy.context.scene, True, 'PREVIEW', calc_tessface=False)
        bm = bmesh.new()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    else:
        me = obj.data
        if obj.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    # Remove custom data layers to save memory
    for elem in (bm.faces, bm.edges, bm.verts, bm.loops):
        for layers_name in dir(elem.layers):
            if not layers_name.startswith("_"):
                layers = getattr(elem.layers, layers_name)
                for layer_name, layer in layers.items():
                    layers.remove(layer)

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm

def local_to_world(cords, world):
    """
    :param cords: coordinates a tuple of 3 values for x,y,z
    :param world: world matrix <- transformation matrix
    Returns a cords transformed to the given transformation world matrix
    """
    return [world @ Vector(cord) for cord in cords]

def get_bounds(obj):
    """
    :param obj: a mesh object
    :returns [8x[3xfloat]] the object aligned bounding box coordinates in world coordinates
    """
    return local_to_world(obj.bound_box, obj.matrix_world)

def dot_product(v1,v2):
    """
    :param v1: a vector of 3 scalars
    :param v2: a vector of 3 scalars
    returns dot product between the vectors
    """
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

def check_bb_intersection(obj1,obj2):
    """
    :param obj1: object 1  to check for intersection, must be a mesh
    :param obj2: object 2  to check for intersection, must be a mesh
    Checks if there is a bounding box collision, these don't have to be axis-aligned, but if they are not:
        The enclosing axis-aligned bounding box is calculated and used to check the intersection
    returns a boolean
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
    collide = True
    for min_b1_val, max_b1_val, min_b2_val, max_b2_val in zip(min_b1, max_b1, min_b2, max_b2):
        # inspired by this:
        # https://stackoverflow.com/questions/20925818/algorithm-to-check-if-two-boxes-overlap
        # Checks in each dimension, if there is an overlap if this happens it must be an overlap in 3D, too.
        def is_overlapping_1D(x_min_1, x_max_1, x_min_2, x_max_2):
            # returns true if the min and max values are overlapping
            return x_max_1 >= x_min_2 and x_max_2 >= x_min_1
        collide = collide and is_overlapping_1D(min_b1_val, max_b1_val, min_b2_val, max_b2_val)
    return collide


def check_intersection(obj, obj2, cache = None):
    """
    :param obj1: object 1 to check for intersection, must be a mesh
    :param obj2: object 2 to check for intersection, must be a mesh
    Check if any faces intersect with the other object
    returns a boolean
    """
    # refer to https://blender.stackexchange.com/questions/9073/how-to-check-if-two-meshes-intersect-in-python
    assert(obj != obj2)

    if cache is None:
        cache = {}
    
    assert(type(cache) == type({})) # cache must be a dict

    # Triangulate (Load from cache if available)
    if obj.name in cache:
        bm = cache[obj.name]
    else:
        bm = triangulate(obj, transform=True, triangulate=True)
        cache[obj.name] = bm

    if obj2.name in cache:
        bm = cache[obj2.name]
    else:
        bm2 = triangulate(obj2, transform=True, triangulate=True)
        cache[obj2.name] = bm2

    # If bm has more edges, use bm2 instead for looping over its edges
    # (so we cast less rays from the simpler object to the more complex object)
    if len(bm.edges) > len(bm2.edges):
        bm2, bm = bm, bm2

    # Create a real mesh 
    scene = bpy.context.scene
    me_tmp = bpy.data.meshes.new(name="~temp~")
    bm2.to_mesh(me_tmp)
    bm2.free()
    obj_tmp = bpy.data.objects.new(name=me_tmp.name, object_data=me_tmp)
    #scene.objects.link(obj_tmp)
    # refer https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Scene_and_Object_API
    scene.collection.objects.link(obj_tmp) # add object to scene
    #scene.update() # depretiated
    bpy.context.view_layer.update() # new method to udpate scene

    ray_cast = obj_tmp.ray_cast

    intersect = False

    EPS_NORMAL = 0.000001
    EPS_CENTER = 0.01  # should always be bigger

    #for ed in me_tmp.edges:
    for ed in bm.edges:
        v1, v2 = ed.verts

        # setup the edge with an offset
        co_1 = v1.co.copy()
        co_2 = v2.co.copy()
        co_mid = (co_1 + co_2) * 0.5
        no_mid = (v1.normal + v2.normal).normalized() * EPS_NORMAL
        co_1 = co_1.lerp(co_mid, EPS_CENTER) + no_mid
        co_2 = co_2.lerp(co_mid, EPS_CENTER) + no_mid

        t, co, no, index = ray_cast(co_1, (co_2 - co_1).normalized(), distance=ed.calc_length())
        if index != -1:
            intersect = True
            break

    scene.collection.objects.unlink(obj_tmp)
    bpy.data.objects.remove(obj_tmp)
    bpy.data.meshes.remove(me_tmp)

    # new method to udpate scene
    bpy.context.view_layer.update()

    return intersect

def vector_to_euler(vector, vector_type):
    """
    :param vector: UP (for MESH objs) of FORWARD (for LIGHT/CAMERA objs) vector. Type: mathutils Vector.
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
    :return the generated obj
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

def add_cube_based_on_bb(bouding_box, name='NewCube'):
    """
    Generates a cube based on the given bounding box, the bounding_box can be generated with our get_bounds(obj) fct.

    :param bounding_box: bound_box [8x[3xfloat]], with 8 vertices for each corner
    :param name: name of the new cube
    :return the generated object
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

