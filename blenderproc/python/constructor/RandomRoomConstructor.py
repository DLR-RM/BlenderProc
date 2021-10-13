import warnings
import math
from typing import Tuple, List, Dict

import bpy
import bmesh
import mathutils
import numpy as np
import random

from blenderproc.python.modules.provider.getter.Material import Material
from blenderproc.python.utility.CollisionUtility import CollisionUtility
from blenderproc.python.types.EntityUtility import Entity, delete_multiple
from blenderproc.python.types.MeshObjectUtility import MeshObject, create_primitive
from blenderproc.python.object.FloorExtractor import FloorExtractor


def construct_random_room(used_floor_area: float, interior_objects: List[MeshObject], materials: List[Material],
                          amount_of_extrusions: int = 0, fac_from_square_room: float = 0.3, corridor_width: float = 0.9,
                          wall_height: float = 2.5, amount_of_floor_cuts: int = 2, only_use_big_edges: bool = True,
                          create_ceiling: bool = True, assign_material_to_ceiling: bool = False,
                          placement_tries_per_face: int = 3,
                          amount_of_objects_per_sq_meter: float = 3.0):
    # internally the first basic rectangular is counted as one
    amount_of_extrusions += 1

    bvh_cache_for_intersection: Dict[str, mathutils.bvhtree.BVHTree] = {}
    placed_objects = []

    # construct a random room
    floor_obj, wall_obj, ceiling_obj = _construct_random_room(used_floor_area, amount_of_extrusions,
                                                             fac_from_square_room, corridor_width,
                                                             wall_height, amount_of_floor_cuts,
                                                             only_use_big_edges, create_ceiling)
    placed_objects.append(wall_obj)
    if ceiling_obj is not None:
        placed_objects.append(ceiling_obj)

    # assign materials to all existing objects
    _assign_materials_to_floor_wall_ceiling(floor_obj, wall_obj, ceiling_obj,
                                           assign_material_to_ceiling, materials)

    # get all floor faces and save their size and bounding box for the round robin
    floor_obj.edit_mode()
    bm = floor_obj.mesh_as_bmesh()
    bm.faces.ensure_lookup_table()

    list_of_face_sizes = []
    list_of_face_bb = []
    for face in bm.faces:
        list_of_face_sizes.append(face.calc_area())
        list_of_verts = [v.co for v in face.verts]
        bb_min_point, bb_max_point = np.min(list_of_verts, axis=0), np.max(list_of_verts, axis=0)
        list_of_face_bb.append((bb_min_point, bb_max_point))
    floor_obj.update_from_bmesh(bm)
    floor_obj.object_mode()
    bpy.ops.object.select_all(action='DESELECT')
    total_face_size = sum(list_of_face_sizes)

    # sort them after size
    interior_objects.sort(key=lambda obj: obj.get_bound_box_volume())
    interior_objects.reverse()

    list_of_deleted_objects = []

    step_size = 1.0 / amount_of_objects_per_sq_meter * float(len(interior_objects))
    current_step_size_counter = random.uniform(-step_size, step_size)
    for selected_obj in interior_objects:
        current_obj = selected_obj
        is_duplicated = False

        # if the step size is bigger than the room size, certain objects need to be skipped
        if step_size > total_face_size:
            current_step_size_counter += total_face_size
            if current_step_size_counter > step_size:
                current_step_size_counter = random.uniform(-step_size, step_size)
                continue

        # walk over all faces in a round robin fashion
        total_acc_size = 0
        # select a random start point
        current_i = random.randrange(len(list_of_face_sizes))
        current_accumulated_face_size = random.uniform(0, step_size + 1e-7)
        # check if the accumulation of all visited faces is bigger than the sum of all of them
        while total_acc_size < total_face_size:
            face_size = list_of_face_sizes[current_i]
            face_bb = list_of_face_bb[current_i]
            if face_size < step_size:
                # face size is bigger than one step
                current_accumulated_face_size += face_size
                if current_accumulated_face_size > step_size:
                    for _ in range(placement_tries_per_face):
                        found_spot = _sample_new_object_poses_on_face(current_obj, face_bb,
                                                                     bvh_cache_for_intersection,
                                                                     placed_objects, wall_obj)
                        if found_spot:
                            placed_objects.append(current_obj)
                            current_obj = current_obj.duplicate()
                            is_duplicated = True
                            break
                    current_accumulated_face_size -= step_size
            else:
                # face size is bigger than one step
                amount_of_steps = int((face_size + current_accumulated_face_size) / step_size)
                for i in range(amount_of_steps):
                    for _ in range(placement_tries_per_face):
                        found_spot = _sample_new_object_poses_on_face(current_obj, face_bb,
                                                                     bvh_cache_for_intersection,
                                                                     placed_objects, wall_obj)
                        if found_spot:
                            placed_objects.append(current_obj)
                            current_obj = current_obj.duplicate()
                            is_duplicated = True
                            break
                # left over value is used in next round
                current_accumulated_face_size = face_size - (amount_of_steps * step_size)
            current_i = (current_i + 1) % len(list_of_face_sizes)
            total_acc_size += face_size

        # remove current obj from the bvh cache
        if current_obj.get_name() in bvh_cache_for_intersection:
            del bvh_cache_for_intersection[current_obj.get_name()]
        # if there was no collision save the object in the placed list
        if is_duplicated:
            # delete the duplicated object
            list_of_deleted_objects.append(current_obj)

    # Add the loaded objects, which couldn't be placed
    list_of_deleted_objects.extend([obj for obj in interior_objects if obj not in placed_objects])
    # Delete them all
    delete_multiple(list_of_deleted_objects)

    if floor_obj is not None:
        placed_objects.append(floor_obj)
    return placed_objects


def _construct_random_room(used_floor_area: float, amount_of_extrusions: int, fac_from_square_room: float,
                           corridor_width: float, wall_height: float, amount_of_floor_cuts: int,
                           only_use_big_edges: bool, create_ceiling: bool) -> Tuple[MeshObject, MeshObject, MeshObject]:
    """
    This function constructs the floor plan and builds up the wall. This can be more than just a rectangular shape.

    If `amount_of_extrusions` is bigger than zero, the basic rectangular shape is extended, by first performing
    random cuts in this base rectangular shape along the axis. Then one of the edges is randomly selected and
    from there it is extruded outwards to get to the desired `floor_area`. This process is repeated
    `amount_of_extrusions` times. It might be that a room has less than the desired `amount_of_extrusions` if
    the random splitting reaches the `floor_area` beforehand.
    """
    floor_obj = None
    wall_obj = None
    ceiling_obj = None

    # if there is more than one extrusions, the used floor area must be split over all sections
    # the first section should be at least 50% - 80% big, after that the size depends on the amount of left
    # floor values
    if amount_of_extrusions > 1:
        size_sequence = []
        running_sum = 0.0
        start_minimum = 0.0
        for i in range(amount_of_extrusions - 1):
            if i == 0:
                size_sequence.append(random.uniform(0.4, 0.8))
                start_minimum = (1.0 - size_sequence[-1]) / amount_of_extrusions
            else:
                if start_minimum < 1.0 - running_sum:
                    size_sequence.append(random.uniform(start_minimum, 1.0 - running_sum))
                else:
                    break
            running_sum += size_sequence[-1]
        if 1.0 - running_sum > 1e-7:
            size_sequence.append(1.0 - running_sum)
        if amount_of_extrusions != len(size_sequence):
            print("Amount of extrusions was reduced to: {}. To avoid rooms, which are smaller "
                  "than 1e-7".format(len(size_sequence)))
            amount_of_extrusions = len(size_sequence)
    else:
        size_sequence = [1.0]
    # this list of areas is then used to calculate the extrusions
    # if there is only one element in there, it will create a rectangle
    used_floor_areas = [size * used_floor_area for size in size_sequence]

    # calculate the squared room length for the base room
    squared_room_length = np.sqrt(used_floor_areas[0])
    # create a new plane and rename it to Wall
    wall_obj = create_primitive("PLANE")
    wall_obj.set_name("Wall")

    # calculate the side length of the base room, for that the `fac_from_square_room` is used
    room_length_x = fac_from_square_room * random.uniform(-1, 1) * squared_room_length + squared_room_length
    # make sure that the floor area is still used
    room_length_y = used_floor_areas[0] / room_length_x
    # change the plane to this size
    wall_obj.edit_mode()
    bpy.ops.transform.resize(value=(room_length_x * 0.5, room_length_y * 0.5, 1))
    wall_obj.object_mode()

    def cut_plane(plane: MeshObject):
        """
        Cuts the floor plane in several pieces randomly. This is used for selecting random edges for the extrusions
        later on. This function assumes the current `plane` object is already selected and no other object is
        selected.

        :param plane: The object, which should be split in edit mode.
        """

        # save the size of the plane to determine a best split value
        x_size = plane.get_scale()[0]
        y_size = plane.get_scale()[1]

        # switch to edit mode and select all faces
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # convert plane to BMesh object
        bm = plane.mesh_as_bmesh(True)
        bm.faces.ensure_lookup_table()
        # find all selected edges
        edges = [e for e in bm.edges if e.select]

        biggest_face_id = np.argmax([f.calc_area() for f in bm.faces])
        biggest_face = bm.faces[biggest_face_id]
        # find the biggest face
        faces = [f for f in bm.faces if f == biggest_face]
        geom = []
        geom.extend(edges)
        geom.extend(faces)

        # calculate cutting point
        cutting_point = [x_size * random.uniform(-1, 1), y_size * random.uniform(-1, 1), 0]
        # select a random axis to specify in which direction to cut
        direction_axis = [1, 0, 0] if random.uniform(0, 1) < 0.5 else [0, 1, 0]

        # cut the plane and update the final mesh
        bmesh.ops.bisect_plane(bm, dist=0.01, geom=geom, plane_co=cutting_point, plane_no=direction_axis)
        plane.update_from_bmesh(bm)

    # for each floor cut perform one cut_plane
    for i in range(amount_of_floor_cuts):
        cut_plane(wall_obj)

    # do several extrusions of the basic floor plan, the first one is always the basic one
    for i in range(1, amount_of_extrusions):
        # Change to edit mode of the selected floor
        wall_obj.edit_mode()
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = wall_obj.mesh_as_bmesh()
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        # calculate the size of all edges and find all edges, which are wider than the minimum corridor_width
        # to avoid that super small, super long pieces are created
        boundary_edges = [e for e in bm.edges if e.is_boundary]
        boundary_sizes = [(e, e.calc_length()) for e in boundary_edges]
        boundary_sizes = [(e, s) for e, s in boundary_sizes if s > corridor_width]

        if len(boundary_sizes) > 0:
            # sort the boundaries to focus only on the big ones
            boundary_sizes.sort(key=lambda e: e[1])
            if only_use_big_edges:
                # only select the bigger half of the selected boundaries
                half_size = len(boundary_sizes) // 2
            else:
                # use any of the selected boundaries
                half_size = 0
            used_edges = [e for e, s in boundary_sizes[half_size:]]

            random_edge = None
            shift_vec = None
            edge_counter = 0
            random_index = random.randrange(len(used_edges))
            while edge_counter < len(used_edges):
                # select a random edge from the choose edges
                random_edge = used_edges[random_index]
                # get the direction of the current edge
                direction = np.abs(random_edge.verts[0].co - random_edge.verts[1].co)
                # the shift value depends on the used_floor_area size
                shift_value = used_floor_areas[i] / random_edge.calc_length()

                # depending if the random edge is aligned with the x-axis or the y-axis,
                # the shift is the opposite direction
                if direction[0] == 0:
                    x_shift, y_shift = shift_value, 0
                else:
                    x_shift, y_shift = 0, shift_value
                # calculate the vertices for the new face
                shift_vec = mathutils.Vector([x_shift, y_shift, 0])
                dir_found = False
                for tested_dir in [1, -1]:
                    shift_vec *= tested_dir
                    new_verts = [e.co for e in random_edge.verts]
                    new_verts.extend([e + shift_vec for e in new_verts])
                    new_verts = np.array(new_verts)

                    # check if the newly constructed face is colliding with one of the others
                    # if so generate a new face
                    collision_face_found = False
                    for existing_face in bm.faces:
                        existing_verts = np.array([v.co for v in existing_face.verts])
                        if CollisionUtility.check_bb_intersection_on_values(np.min(existing_verts, axis=0)[:2],
                                                           np.max(existing_verts, axis=0)[:2],
                                                           np.min(new_verts, axis=0)[:2],
                                                           np.max(new_verts, axis=0)[:2],
                                                           # by using this check an edge collision is ignored
                                                           used_check=lambda a, b: a > b):
                            collision_face_found = True
                            break
                    if not collision_face_found:
                        dir_found = True
                        break
                if dir_found:
                    break
                random_index = (random_index + 1) % len(used_edges)
                edge_counter += 1
                random_edge = None

            if random_edge is None:
                for e in used_edges:
                    e.select = True
                raise Exception("No edge found to extrude up on! The reason might be that there are to many cuts"
                                "in the basic room or that the corridor width is too high.")
            # extrude this edge with the calculated shift
            random_edge.select = True
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip": False,
                                                                     "use_dissolve_ortho_edges": False,
                                                                     "mirror": False},
                                             TRANSFORM_OT_translate={"value": shift_vec,
                                                                     "orient_type": 'GLOBAL'})
        else:
            raise Exception("The corridor width is so big that no edge could be selected, "
                            "reduce the corridor width or reduce the amount of floor cuts.")
        # remove all doubles vertices, which might occur
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action='DESELECT')
        wall_obj.update_from_bmesh(bm)
        wall_obj.object_mode()

    # create walls based on the outer shell
    wall_obj.edit_mode()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bm = wall_obj.mesh_as_bmesh()
    bm.edges.ensure_lookup_table()

    # select all edges
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    for e in boundary_edges:
        e.select = True
    # extrude all boundary edges to create the walls
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, wall_height)})
    wall_obj.update_from_bmesh(bm)
    wall_obj.object_mode()

    def extract_plane_from_room(obj: MeshObject, used_split_height: float, up_vec: mathutils.Vector,
                                new_name_for_obj: str):
        """
        Extract a plane from the current room object. This uses the FloorExtractor Module functions

        :param obj: The current room object
        :param used_split_height: The height at which the split should be performed. Usually 0 or wall_height
        :param up_vec: The up_vec corresponds to the face.normal of the selected faces
        :param new_name_for_obj: This will be the new name of the created object
        :return: (bool, bpy.types.Object): Returns True if the object was split and also returns the object. \
                                           Else it returns (False, None).
        """
        compare_height = 0.15
        compare_angle = math.radians(7.5)
        obj.edit_mode()
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = obj.mesh_as_bmesh()
        bm.faces.ensure_lookup_table()
        # Select faces at given height that should be separate from the mesh
        counter = FloorExtractor.select_at_height_value(bm, used_split_height, compare_height,
                                                        mathutils.Vector(up_vec), compare_angle,
                                                        obj.get_local2world_mat())
        # if any faces are selected split them up
        if counter:
            bpy.ops.mesh.separate(type='SELECTED')
            obj.update_from_bmesh(bm)
            obj.object_mode()
            cur_selected_objects = bpy.context.selected_objects
            if cur_selected_objects:
                if len(cur_selected_objects) == 2:
                    cur_selected_objects = [o for o in cur_selected_objects
                                            if o != bpy.context.view_layer.objects.active]
                    cur_selected_objects[0].name = new_name_for_obj
                    cur_created_obj = MeshObject(cur_selected_objects[0])
                else:
                    raise Exception("There is more than one selection after splitting, this should not happen!")
            else:
                raise Exception("No floor object was constructed!")
            bpy.ops.object.select_all(action='DESELECT')
            return True, cur_created_obj
        else:
            obj.object_mode()
            bpy.ops.object.select_all(action='DESELECT')
            return False, None

    # if only one rectangle was created, the wall extrusion creates a full room with ceiling and floor, if not
    # only the floor gets created and the ceiling is missing
    only_rectangle_mode = False
    for used_split_height in [(0, "Floor", [0, 0, 1]), (wall_height, "Ceiling", [0, 0, -1])]:
        created, created_obj = extract_plane_from_room(wall_obj, used_split_height[0], used_split_height[2],
                                                       used_split_height[1])
        if not created and used_split_height[1] == "Floor":
            only_rectangle_mode = True
            break
        elif created and created_obj is not None:
            if "Floor" == used_split_height[1]:
                floor_obj = created_obj
            elif "Ceiling" == used_split_height[1]:
                ceiling_obj = created_obj

    if only_rectangle_mode:
        # in this case the floor and ceiling are pointing outwards, so that normals have to be flipped
        for used_split_height in [(0, "Floor", [0, 0, -1]), (wall_height, "Ceiling", [0, 0, 1])]:
            created, created_obj = extract_plane_from_room(wall_obj, used_split_height[0],
                                                           used_split_height[2],
                                                           used_split_height[1])
            # save the result accordingly
            if created and created_obj is not None:
                if "Floor" == used_split_height[1]:
                    floor_obj = created_obj
                elif "Ceiling" == used_split_height[1]:
                    ceiling_obj = created_obj
    elif create_ceiling:
        # there is no ceiling -> create one
        wall_obj.edit_mode()
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = wall_obj.mesh_as_bmesh()
        bm.edges.ensure_lookup_table()
        # select all upper edges and create a ceiling
        for e in bm.edges:
            if ((e.verts[0].co + e.verts[1].co) * 0.5)[2] >= wall_height - 1e-4:
                e.select = True
        bpy.ops.mesh.edge_face_add()
        # split the ceiling away
        bpy.ops.mesh.separate(type='SELECTED')
        wall_obj.update_from_bmesh(bm)
        wall_obj.object_mode()
        selected_objects = bpy.context.selected_objects
        if selected_objects:
            if len(selected_objects) == 2:
                selected_objects = [o for o in selected_objects
                                    if o != bpy.context.view_layer.objects.active]
                selected_objects[0].name = "Ceiling"
                ceiling_obj = MeshObject(selected_objects[0])
            else:
                raise Exception("There is more than one selection after splitting, this should not happen!")
        else:
            raise Exception("No floor object was constructed!")
        bpy.ops.object.select_all(action='DESELECT')

    return floor_obj, wall_obj, ceiling_obj


def _assign_materials_to_floor_wall_ceiling(floor_obj: MeshObject, wall_obj: MeshObject, ceiling_obj: MeshObject,
                                            assign_material_to_ceiling: bool, materials: List[Material]):
    """
    Assigns materials to the floor, wall and ceiling. These are randomly selected from the CCMaterials. This means
    it is required that the CCMaterialLoader has been executed before, this module is run.
    """

    # first create a uv mapping for each of the three objects
    for obj in [floor_obj, wall_obj, ceiling_obj]:
        if obj is not None:
            obj.edit_mode()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.cube_project(cube_size=1.0)
            obj.object_mode()

    if materials:
        floor_obj.replace_materials(random.choice(materials))
        wall_obj.replace_materials(random.choice(materials))
        if ceiling_obj is not None and assign_material_to_ceiling:
            ceiling_obj.replace_materials(random.choice(materials))
    else:
        warnings.warn("There were no CCMaterials found, which means the CCMaterialLoader was not executed first!"
                      "No materials have been assigned to the walls, floors and possible ceiling.")


def _sample_new_object_poses_on_face(current_obj: MeshObject, face_bb, bvh_cache_for_intersection: dict,
                                     placed_objects: List[MeshObject], wall_obj: MeshObject):
    """
    Sample new object poses on the current `floor_obj`.

    :param face_bb:
    :return: True, if there is no collision
    """
    random_placed_value = [random.uniform(face_bb[0][i], face_bb[1][i]) for i in range(2)]
    random_placed_value.append(0.0)  # floor z value

    random_placed_rotation = [0, 0, random.uniform(0, np.pi * 2.0)]

    current_obj.set_location(random_placed_value)
    current_obj.set_rotation_euler(random_placed_rotation)

    # Remove bvh cache, as object has changed
    if current_obj.get_name() in bvh_cache_for_intersection:
        del bvh_cache_for_intersection[current_obj.get_name()]

    # perform check if object can be placed there
    no_collision = CollisionUtility.check_intersections(current_obj,
                                                        bvh_cache=bvh_cache_for_intersection,
                                                        objects_to_check_against=placed_objects,
                                                        list_of_objects_with_no_inside_check=[wall_obj])
    return no_collision
