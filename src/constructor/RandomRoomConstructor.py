import warnings
import math

import bpy
import bmesh
import mathutils
import numpy as np
import random

from src.main.Module import Module
from src.object.FloorExtractor import FloorExtractor
from src.object.ObjectPoseSampler import ObjectPoseSampler
from src.provider.getter.Material import Material
from src.utility.BlenderUtility import get_bound_volume, check_bb_intersection_on_values
from src.utility.Utility import Utility, Config


class RandomRoomConstructor(Module):
    """
    This module constructs random rooms with different dataset objects.
    It first samples a random room, uses CCMaterial on the surfaces, which contain no alpha textures, to avoid that the
    walls or the floor is see through.

    Then this room is randomly filled with the objects from the proposed datasets.

    It is possible to randomly construct rooms, which are not rectangular shaped, for that you can use the key
    `amount_of_extrusions`, zero is the default, which means that the room will get no extrusions, if you specify, `3`
    then the room will have up to 3 corridors or bigger pieces extruding from the main rectangular.

    Example 1, in this first example a random room will be constructed it will have a floor area of 20 square meters.
    The room will then be filled with 15 randomly selected objects from the IKEA dataset, belonging to the categories
    "bed" and "chair". Checkout the `examples/ikea` if you want to know more on that particular dataset.

    .. code-block:: yaml

        {
          "module": "constructor.RandomRoomConstructor",
          "config": {
            "floor_area": 20,
            "used_loader_config": [
              {
                "module": "loader.IKEALoader",
                "config": {
                  "category": ["bed", "chair"]
                },
                "amount_of_repetitions": 15
              }
            ]
          }
        }

    **Configuration**:

    .. list-table::
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - floor_area
          - The amount of floor area used for the created room, the value is specified in square meters.
          - float
        * - amount_of_extrusions
          - The amount of extrusions specify how many times the room will be extruded to form more complicated shapes
            than single rectangles. The default is zero, which means that no extrusion is performed and the room consist
            out of one single rectangle. Default: 0.
          - int
        * - fac_base_from_square_room
          - After creating a squared room, the room is reshaped to a rectangular, this factor determines the maximum
            difference in positive and negative direction from the squared rectangular. This means it looks like this:
            `fac * rand.uniform(-1, 1) * square_len + square_len`. Default: 0.3.
          - float
        * - minimum_corridor_width
          - The minimum corridor width of an extrusions, this is used to avoid that extrusions are super slim.
            Default: 0.9.
          - float
        * - wall_height
          - This value specifies the height of the wall in meters. Default: 2.5.
          - float
        * - amount_of_floor_cuts
          - This value determines how often the basic rectangle is cut vertically and horizontally. These cuts are than
            used for selecting the edges which are then extruded. A higher amount of floor cuts leads to smaller edges,
            if all edges are smaller than the corridor width no edge will be selected. Default: 2.
          - int
        * - only_use_big_edges
          - If this is set to true, all edges, which are wider than the corridor width are sorted by their size and
            then only the bigger half of this list is used. If this is false, the full sorted array is used.
            Default: True.
          - bool
        * - create_ceiling
          - If this is True, the ceiling is created as its own object. If this is False no ceiling will be created.
            Default: True.
          - bool
        * - assign_material_to_ceiling
          - If this is True a material from the CCMaterial set is assigned to the ceiling. This is only possible if a
            ceiling was created. Default: False.
          - bool
        * - placement_tries_per_face
          - The amount of tries, which are performed per floor segment to place an object, a higher number, will
            get a better accuracy on the `amount_of_objects_per_sq_meter` value. But, it will also increase the
            computation time. Default: 3.
          - int
        * - amount_of_objects_per_sq_meter
          - The amount of objects, which should be placed in one square meter, this value is only used as approximation.
            Especially, if the objects have very different sizes this might lead to different results. Default: 3.0
          - float
    """

    def __init__(self, config: Config):
        """
        This function is called by the Pipeline object, it initialized the object and reads all important config values

        :param config: The config object used for this module, specified by the .yaml file
        """
        Module.__init__(self, config)

        self.bvh_cache_for_intersection = {}
        self.placed_objects = []

        self.used_floor_area = self.config.get_float("floor_area")
        self.amount_of_extrusions = self.config.get_int("amount_of_extrusions", 0)
        self.fac_from_square_room = self.config.get_float("fac_base_from_square_room", 0.3)
        self.corridor_width = self.config.get_float("minimum_corridor_width", 0.9)
        self.wall_height = self.config.get_float("wall_height", 2.5)
        # internally the first basic rectangular is counted as one
        self.amount_of_extrusions += 1
        self.amount_of_floor_cuts = self.config.get_int("amount_of_floor_cuts", 2)
        self.only_use_big_edges = self.config.get_bool("only_use_big_edges", True)
        self.create_ceiling = self.config.get_bool("create_ceiling", True)
        self.assign_material_to_ceiling = self.config.get_bool("assign_material_to_ceiling", False)
        self.tries_per_face = self.config.get_int("placement_tries_per_face", 3)
        self.amount_of_objects_per_sq_meter = self.config.get_float("amount_of_objects_per_sq_meter", 3.0)

        self.wall_obj = None
        self.floor_obj = None
        self.ceiling_obj = None

    def construct_random_room(self):
        """
        This function constructs the floor plan and builds up the wall. This can be more than just a rectangular shape.

        If `amount_of_extrusions` is bigger than zero, the basic rectangular shape is extended, by first performing
        random cuts in this base rectangular shape along the axis. Then one of the edges is randomly selected and
        from there it is extruded outwards to get to the desired `floor_area`. This process is repeated
        `amount_of_extrusions` times. It might be that a room has less than the desired `amount_of_extrusions` if
        the random splitting reaches the `floor_area` beforehand.
        """

        # if there is more than one extrusions, the used floor area must be split over all sections
        # the first section should be at least 50% - 80% big, after that the size depends on the amount of left
        # floor values
        if self.amount_of_extrusions > 1:
            size_sequence = []
            running_sum = 0.0
            start_minimum = 0.0
            for i in range(self.amount_of_extrusions - 1):
                if i == 0:
                    size_sequence.append(random.uniform(0.4, 0.8))
                    start_minimum = (1.0 - size_sequence[-1]) / self.amount_of_extrusions
                else:
                    if start_minimum < 1.0 - running_sum:
                        size_sequence.append(random.uniform(start_minimum, 1.0 - running_sum))
                    else:
                        break
                running_sum += size_sequence[-1]
            if 1.0 - running_sum > 1e-7:
                size_sequence.append(1.0 - running_sum)
            if self.amount_of_extrusions != len(size_sequence):
                print("Amount of extrusions was reduced to: {}. To avoid rooms, which are smaller "
                      "than 1e-7".format(len(size_sequence)))
                self.amount_of_extrusions = len(size_sequence)
        else:
            size_sequence = [1.0]
        # this list of areas is then used to calculate the extrusions
        # if there is only one element in there, it will create a rectangle
        used_floor_areas = [size * self.used_floor_area for size in size_sequence]

        # calculate the squared room length for the base room
        squared_room_length = np.sqrt(used_floor_areas[0])
        # create a new plane and rename it to Floor
        bpy.ops.mesh.primitive_plane_add()
        self.wall_obj: bpy.types.Object = bpy.context.object
        self.wall_obj.name = "Wall"

        # calculate the side length of the base room, for that the `fac_from_square_room` is used
        room_length_x = self.fac_from_square_room * random.uniform(-1, 1) * squared_room_length + squared_room_length
        # make sure that the floor area is still used
        room_length_y = used_floor_areas[0] / room_length_x
        # change the plane to this size
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=(room_length_x * 0.5, room_length_y * 0.5, 1))
        bpy.ops.object.mode_set(mode='OBJECT')

        def cut_plane(plane: bpy.types.Object):
            """
            Cuts the floor plane in several pieces randomly. This is used for selecting random edges for the extrusions
            later on. This function assumes the current `plane` object is already selected and no other object is
            selected.

            :param plane: The object, which should be split in edit mode.
            """

            # save the size of the plane to determine a best split value
            x_size = plane.scale[0]
            y_size = plane.scale[1]

            # switch to edit mode and select all faces
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            # convert plane to BMesh object
            me = plane.data
            bm = bmesh.new()
            bm.from_mesh(me)
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
            bm.to_mesh(me)
            bm.free()
            me.update()

        # for each floor cut perform one cut_plane
        for i in range(self.amount_of_floor_cuts):
            cut_plane(self.wall_obj)

        mesh = self.wall_obj.data
        # do several extrusions of the basic floor plan, the first one is always the basic one
        for i in range(1, self.amount_of_extrusions):
            # Change to edit mode of the selected floor
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bm = bmesh.from_edit_mesh(mesh)
            bm.faces.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            # calculate the size of all edges and find all edges, which are wider than the minimum corridor_width
            # to avoid that super small, super long pieces are created
            boundary_edges = [e for e in bm.edges if e.is_boundary]
            boundary_sizes = [(e, e.calc_length()) for e in boundary_edges]
            boundary_sizes = [(e, s) for e, s in boundary_sizes if s > self.corridor_width]

            if len(boundary_sizes) > 0:
                # sort the boundaries to focus only on the big ones
                boundary_sizes.sort(key=lambda e: e[1])
                if self.only_use_big_edges:
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
                            if check_bb_intersection_on_values(np.min(existing_verts, axis=0)[:2],
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
            bpy.ops.object.mode_set(mode='OBJECT')
            bm.free()
            mesh.update()

        # create walls based on the outer shell
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bm = bmesh.from_edit_mesh(mesh)
        bm.edges.ensure_lookup_table()

        # select all edges
        boundary_edges = [e for e in bm.edges if e.is_boundary]
        for e in boundary_edges:
            e.select = True
        # extrude all boundary edges to create the walls
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, self.wall_height)})
        bpy.ops.object.mode_set(mode='OBJECT')
        bm.free()
        mesh.update()

        def extract_plane_from_room(obj: bpy.types.Object, used_split_height: float, up_vec: mathutils.Vector,
                                    new_name_for_obj: str):
            """
            Extract a plane from the current room object. This uses the FloorExtractor Module functions

            :param obj: The current room object
            :param used_split_height: The height at which the split should be performed. Usually 0 or self.wall_height
            :param up_vec: The up_vec corresponds to the face.normal of the selected faces
            :param new_name_for_obj: This will be the new name of the created object
            :return: (bool, bpy.types.Object): Returns True if the object was split and also returns the object. \
                                               Else it returns (False, None).
            """
            compare_height = 0.15
            compare_angle = math.radians(7.5)
            obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bm = bmesh.from_edit_mesh(mesh)
            bm.faces.ensure_lookup_table()
            # split the floor at the wall height
            counter = FloorExtractor.split_at_height_value(bm, used_split_height, compare_height,
                                                           mathutils.Vector(up_vec), compare_angle, obj.matrix_world)
            # if any faces are selected split them up
            if counter:
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')
                bm.free()
                mesh.update()
                cur_selected_objects = bpy.context.selected_objects
                if cur_selected_objects:
                    if len(cur_selected_objects) == 2:
                        cur_selected_objects = [o for o in cur_selected_objects
                                                if o != bpy.context.view_layer.objects.active]
                        cur_selected_objects[0].name = new_name_for_obj
                        cur_created_obj = cur_selected_objects[0]
                    else:
                        raise Exception("There is more than one selection after splitting, this should not happen!")
                else:
                    raise Exception("No floor object was constructed!")
                bpy.ops.object.select_all(action='DESELECT')
                return True, cur_created_obj
            else:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                return False, None

        # if only one rectangle was created, the wall extrusion creates a full room with ceiling and floor, if not
        # only the floor gets created and the ceiling is missing
        only_rectangle_mode = False
        for used_split_height in [(0, "Floor", [0, 0, 1]), (self.wall_height, "Ceiling", [0, 0, -1])]:
            created, created_obj = extract_plane_from_room(self.wall_obj, used_split_height[0], used_split_height[2],
                                                           used_split_height[1])
            if not created and used_split_height[1] == "Floor":
                only_rectangle_mode = True
                break
            elif created and created_obj is not None:
                if "Floor" == used_split_height[1]:
                    self.floor_obj = created_obj
                elif "Ceiling" == used_split_height[1]:
                    self.ceiling_obj = created_obj

        if only_rectangle_mode:
            # in this case the floor and ceiling are pointing outwards, so that normals have to be flipped
            for used_split_height in [(0, "Floor", [0, 0, -1]), (self.wall_height, "Ceiling", [0, 0, 1])]:
                created, created_obj = extract_plane_from_room(self.wall_obj, used_split_height[0],
                                                               used_split_height[2],
                                                               used_split_height[1])
                # save the result accordingly
                if created and created_obj is not None:
                    if "Floor" == used_split_height[1]:
                        self.floor_obj = created_obj
                    elif "Ceiling" == used_split_height[1]:
                        self.ceiling_obj = created_obj
        elif self.create_ceiling:
            # there is no ceiling -> create one
            self.wall_obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bm = bmesh.from_edit_mesh(mesh)
            bm.edges.ensure_lookup_table()
            # select all upper edges and create a ceiling
            for e in bm.edges:
                if ((e.verts[0].co + e.verts[1].co) * 0.5)[2] >= self.wall_height:
                    e.select = True
            bpy.ops.mesh.edge_face_add()
            # split the ceiling away
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            bm.free()
            mesh.update()
            selected_objects = bpy.context.selected_objects
            if selected_objects:
                if len(selected_objects) == 2:
                    selected_objects = [o for o in selected_objects
                                        if o != bpy.context.view_layer.objects.active]
                    selected_objects[0].name = "Ceiling"
                    self.ceiling_obj = selected_objects[0]
                else:
                    raise Exception("There is more than one selection after splitting, this should not happen!")
            else:
                raise Exception("No floor object was constructed!")
            bpy.ops.object.select_all(action='DESELECT')

    def assign_materials_to_floor_wall_ceiling(self):
        """
        Assigns materials to the floor, wall and ceiling. These are randomly selected from the CCMaterials. This means
        it is required that the CCMaterialLoader has been executed before, this module is run.
        """

        # first create a uv mapping for each of the three objects
        for obj in [self.floor_obj, self.wall_obj, self.ceiling_obj]:
            if obj is not None:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.cube_project(cube_size=1.0)
                bpy.ops.object.mode_set(mode='OBJECT')

        # only select non see through materials
        config = {"conditions": {"cp_is_cc_texture": True, "cf_principled_bsdf_Alpha_eq": 1.0}}
        material_getter = Material(Config(config))
        all_cc_materials = material_getter.run()

        def assign_material(cur_obj: bpy.types.Object, material: bpy.types.Material):
            """
            First all materials are removed and then the given material is assigned

            :param cur_obj: Current object
            :param material: Current material, which will be assigned
            """
            # first remove all existing
            if cur_obj.material_slots:
                for i in range(len(cur_obj.material_slots)):
                    bpy.ops.object.material_slot_remove({'object': cur_obj})
            # add the new one
            cur_obj.data.materials.append(material)

        if all_cc_materials:
            assign_material(self.floor_obj, random.choice(all_cc_materials))
            assign_material(self.wall_obj, random.choice(all_cc_materials))
            if self.ceiling_obj is not None and self.assign_material_to_ceiling:
                assign_material(self.ceiling_obj, random.choice(all_cc_materials))
        else:
            warnings.warn("There were no CCMaterials found, which means the CCMaterialLoader was not executed first!"
                          "No materials have been assigned to the walls, floors and possible ceiling.")

    def sample_new_object_poses_on_face(self, current_obj, face_bb):
        """
        Sample new object poses on the current `self.floor_obj`.

        :param face_bb:
        :return: True, if there is no collision
        """
        random_placed_value = [random.uniform(face_bb[0][i], face_bb[1][i]) for i in range(2)]
        random_placed_value.append(0.0)  # floor z value

        random_placed_rotation = [0, 0, random.uniform(0, np.pi * 2.0)]

        # perform check if object can be placed there
        no_collision = ObjectPoseSampler.check_pose_for_object(current_obj, position=random_placed_value,
                                                               rotation=random_placed_rotation,
                                                               bvh_cache=self.bvh_cache_for_intersection,
                                                               objects_to_check_against=self.placed_objects,
                                                               list_of_objects_with_no_inside_check=[self.wall_obj])
        return no_collision

    def run(self):
        # construct a random room
        self.construct_random_room()
        self.placed_objects.append(self.wall_obj)
        if self.ceiling_obj is not None:
            self.placed_objects.append(self.ceiling_obj)

        # assign materials to all existing objects
        self.assign_materials_to_floor_wall_ceiling()

        # use a loader module to load objects
        bpy.ops.object.select_all(action='SELECT')
        previously_selected_objects = set(bpy.context.selected_objects)
        module_list_config = self.config.get_list("used_loader_config")
        modules = Utility.initialize_modules(module_list_config)
        for module in modules:
            print("Running module " + module.__class__.__name__)
            module.run()
        bpy.ops.object.select_all(action='SELECT')
        loaded_objects = list(set(bpy.context.selected_objects) - previously_selected_objects)

        # get all floor faces and save their size and bounding box for the round robin
        bpy.ops.object.select_all(action='DESELECT')
        self.floor_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = self.floor_obj.data
        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()

        list_of_face_sizes = []
        list_of_face_bb = []
        for face in bm.faces:
            list_of_face_sizes.append(face.calc_area())
            list_of_verts = [v.co for v in face.verts]
            bb_min_point, bb_max_point = np.min(list_of_verts, axis=0), np.max(list_of_verts, axis=0)
            list_of_face_bb.append((bb_min_point, bb_max_point))
        bpy.ops.object.mode_set(mode='OBJECT')
        bm.free()
        mesh.update()
        bpy.ops.object.select_all(action='DESELECT')
        total_face_size = sum(list_of_face_sizes)

        # sort them after size
        loaded_objects.sort(key=lambda obj: get_bound_volume(obj))
        loaded_objects.reverse()

        list_of_deleted_objects = []

        step_size = 1.0 / self.amount_of_objects_per_sq_meter * float(len(loaded_objects))
        current_step_size_counter = random.uniform(-step_size, step_size)
        for selected_obj in loaded_objects:
            current_obj = selected_obj
            is_duplicated = False

            def duplicate_obj(cur_obj):
                # object was placed before needs to be duplicated first
                bpy.ops.object.duplicate({"object": cur_obj, "selected_objects": [cur_obj]})
                cur_obj = bpy.context.selected_objects[-1]
                return cur_obj

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
                        for _ in range(self.tries_per_face):
                            found_spot = self.sample_new_object_poses_on_face(current_obj, face_bb)
                            if found_spot:
                                self.placed_objects.append(current_obj)
                                current_obj = duplicate_obj(cur_obj=current_obj)
                                is_duplicated = True
                                break
                        current_accumulated_face_size -= step_size
                else:
                    # face size is bigger than one step
                    amount_of_steps = int((face_size + current_accumulated_face_size) / step_size)
                    for i in range(amount_of_steps):
                        for _ in range(self.tries_per_face):
                            found_spot = self.sample_new_object_poses_on_face(current_obj, face_bb)
                            if found_spot:
                                self.placed_objects.append(current_obj)
                                current_obj = duplicate_obj(cur_obj=current_obj)
                                is_duplicated = True
                                break
                    # left over value is used in next round
                    current_accumulated_face_size = face_size - (amount_of_steps * step_size)
                current_i = (current_i + 1) % len(list_of_face_sizes)
                total_acc_size += face_size

            # remove current obj from the bvh cache
            if current_obj.name in self.bvh_cache_for_intersection:
                del self.bvh_cache_for_intersection[current_obj.name]
            # if there was no collision save the object in the placed list
            if is_duplicated:
                # delete the duplicated object
                list_of_deleted_objects.append(current_obj)

        # delete all objects, which have not been placed during the operation
        bpy.ops.object.select_all(action='DESELECT')
        for obj in list_of_deleted_objects:
            obj.select_set(True)

        # delete the loaded objects, which couldn't be placed
        for obj in loaded_objects:
            if obj not in self.placed_objects:
                obj.select_set(True)
        bpy.ops.object.delete()
