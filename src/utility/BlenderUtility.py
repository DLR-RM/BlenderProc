import bpy
import bmesh
from mathutils import Vector

    

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
    returns the 8 axis aligned bounding box coordinates transformed to world matrix
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
    Checks if there is a bounding box collision
    returns a boolean
    """
    b1w = get_bounds(obj1)
    b2w = get_bounds(obj2)
    origins = [[0,3],[0,4],[0,1]]
    deltas = [b1w[origins[0][0]] - b1w[origins[0][1]], b1w[origins[1][0]] - b1w[origins[1][1]], b1w[origins[2][0]] - b1w[origins[2][1]]]
    for point in b2w:
        collide = True
        # check if that point lies inside the area
        # Explanation found at https://math.stackexchange.com/questions/1472049/check-if-a-point-is-inside-a-rectangular-shaped-area-3d
        for idx in range(3): 
            dot_with_query = dot_product(deltas[idx],point)
            dot_with_r1 = dot_product(deltas[idx],b1w[origins[idx][0]])
            dot_with_r2 = dot_product(deltas[idx],b1w[origins[idx][1]])
            collide = collide and (dot_with_r2 < dot_with_query and dot_with_query < dot_with_r1)
        if collide:
            return True
    return False


def check_intersection(obj, obj2, cache = None):
    """
    :param obj1: object 1  to check for intersection, must be a mesh
    :param obj2: object 2  to check for intersection, must be a mesh
    Check if any faces intersect with the other object
    returns a boolean
    """
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

        t, co, no, index = ray_cast(co_1, co_2)
        if index != -1:
            intersect = True
            break

    scene.collection.objects.unlink(obj_tmp)
    bpy.data.objects.remove(obj_tmp)
    bpy.data.meshes.remove(me_tmp)

    # new method to udpate scene
    bpy.context.view_layer.update()

    return intersect, cache

def norm_vector(a, b):
    """
    Returns a normalized vector directing from point A to point B.

    :param a: Point a. Type: mathutils Vector.
    :param a: Point b. Type: mathutils Vector.
    :return: Normilized vector.
    """
    return (a-b)/(a-b).dot(a-b)**(0.5)
