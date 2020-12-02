import bpy
import bmesh
import mathutils
import math
import numpy as np
import random

from src.main.Module import Module
from src.utility.Utility import Utility, Config


class RandomRoomConstructor(Module):
    """
    This module constructs random rooms with different dataset objects.
    It first samples a random room, uses CCMaterial on the surfaces, these do not contain any alpha information.

    Then this room is randomly filled with the objects from the proposed datasets.

    """


    def __init__(self, config):
        Module.__init__(self, config)


    def construct_random_room(self):
        """
        This function constructs the floor plan and builds up the wall
        :return constructed the room object
        """

        used_floor_area = self.config.get_float("floor_area")
        wall_height = self.config.get_float("wall_height", 2.5)
        corridor_width = self.config.get_float("minimum_corridor_width", 0.9)
        amount_of_extrusions = self.config.get_int("amount_of_extrusions", 3)
        fac_from_square_room = self.config.get_float("fac_base_from_square_room", 0.3)
        amount_of_floor_cuts = self.config.get_int("amount_of_floor_cuts", 2)
        only_use_big_edges = self.config.get_bool("only_use_big_edges", True)

        # if there is more than one extrusions, the used floor area must be split over all sections
        # the first section should be at least 50% - 80% big, after that the size depends on the amount of left
        # floor values
        if amount_of_extrusions > 1:
            size_sequence = []
            running_sum = 0.0
            for i in range(amount_of_extrusions - 1):
                if i == 0:
                    size_sequence.append(random.uniform(0.5, 0.8))
                else:
                    size_sequence.append(random.uniform(0, 1.0 - running_sum))
                running_sum += size_sequence[-1]
            size_sequence.append(1.0 - running_sum)
        else:
            size_sequence = [1.0]
        used_floor_areas = [size * used_floor_area for size in size_sequence]

        squared_room_length = np.sqrt(used_floor_areas[0])
        bpy.ops.mesh.primitive_plane_add()
        new_floor = bpy.context.object

        new_floor.name = "Floor"

        room_length_x = fac_from_square_room * random.uniform(-1, 1) * squared_room_length + squared_room_length
        room_length_y = used_floor_areas[0] / room_length_x
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=(room_length_x * 0.5, room_length_y * 0.5, 1))
        bpy.ops.object.mode_set(mode='OBJECT')

        def cut_plane(object):

            x_size = object.scale[0]
            y_size = object.scale[1]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            me = object.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            edges = [e for e in bm.edges if e.select == True]

            biggest_face_id = np.argmax([f.calc_area() for f in bm.faces])
            biggset_face = bm.faces[biggest_face_id]
            faces = [f for f in bm.faces if f == biggset_face]
            geom = []
            geom.extend(edges)
            geom.extend(faces)

            cutting_point = [x_size * random.uniform(-1, 1), y_size * random.uniform(-1, 1),0]
            if random.uniform(0, 1) < 0.5:
                direction_axis = [1,0,0]
            else:
                direction_axis = [0,1,0]

            bmesh.ops.bisect_plane(bm, dist=0.01,geom=geom,plane_co=cutting_point,plane_no=direction_axis)
            bm.to_mesh(me)
            bm.free()
            me.update()
        for i in range(amount_of_floor_cuts):
            cut_plane(new_floor)

        mesh = new_floor.data
        # do several extrusions of the basic floor plan, the first one is always the basic one
        for i in range(1, amount_of_extrusions):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bm = bmesh.from_edit_mesh(mesh)
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
                    half_size = len(boundary_sizes)//2
                else:
                    # use any of the selected boundaries
                    half_size = 0
                used_edges = [e for e, s in boundary_sizes[half_size:]]

                # select a random edge from the choose edges
                random_edge = random.choice(used_edges)
                # get the direction of the current edge
                direction = np.abs(random_edge.verts[0].co - random_edge.verts[1].co)
                # the shift value depends on the used_floor_area size
                shift_value = used_floor_areas[i] / random_edge.calc_length()
                # depending if the random edge is aligned with the x-axis or the y-axis,
                # the shift is the opposite direction
                if direction[0] < direction[1]:
                    x_shift, y_shift = shift_value, 0
                    # flip them if it is negative
                    if random_edge.verts[0].co[0] < 0:
                        x_shift *= -1
                else:
                    x_shift, y_shift = 0, shift_value
                    # flip them if it is negative
                    if random_edge.verts[0].co[1] < 0:
                        y_shift *= -1

                # extrude this edge with the calculated shift
                random_edge.select = True
                bpy.ops.mesh.extrude_region_move( MESH_OT_extrude_region={"use_normal_flip": False,
                                                                          "use_dissolve_ortho_edges": False,
                                                                          "mirror": False},
                                                  TRANSFORM_OT_translate={"value": (x_shift, y_shift, 0),
                                                                          "orient_type": 'GLOBAL'})
            else:
                raise Exception("The corridor width is so big that no edge could be selected, "
                                "reduce the corridor width or reduce the amount of floor cuts.")
            # remove all doubles vertices, which might occur
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bm.free()
            mesh.update()


        # create walls based on the outer shell
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bm = bmesh.from_edit_mesh(mesh)
        bm.edges.ensure_lookup_table()
        boundary_edges = [e for e in bm.edges if e.is_boundary]
        for e in boundary_edges:
            e.select = True
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, wall_height)})
        bpy.ops.object.mode_set(mode='OBJECT')
        bm.free()
        mesh.update()

        # remove the upper ceiling if it was created, sometimes blender creates it, depending if it is a simple
        # rectangle or not
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(mesh)
        up_vec = mathutils.Vector([0,0,1])
        found_face_to_be_deleted = False
        compare_angle = 0.1
        floor_faces = []
        for f in bm.faces:
            f.select = False
            if math.acos(f.normal @ up_vec) < compare_angle:
                if np.abs(f.calc_center_median()[2] - wall_height) < wall_height * 0.1:
                    found_face_to_be_deleted = True
                    f.select = True
                else:
                    # these are floor faces, can be used to set the material
                    floor_faces.append(f)
        if found_face_to_be_deleted:
            bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        bm.free()
        mesh.update()

    def paint_floor_and_wall(self):
        pass


    def run(self):
        # construct a random room
        self.construct_random_room()

        # use a loader module to load objects
        bpy.ops.object.select_all(action='SELECT')
        previously_selected_objects = set(bpy.context.selected_objects)
        module_list_config = self.config.get_list("used_loader_config")
        modules = Utility.initialize_modules(module_list_config)
        for module in modules:
            print("Running module " + module.__class__.__name__)
            module.run()
        loaded_objects = list(set(bpy.context.selected_objects) - previously_selected_objects)
        print(loaded_objects)

