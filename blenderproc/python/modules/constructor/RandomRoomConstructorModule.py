import bpy

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.provider.getter.Material import Material as MaterialProvider
from blenderproc.python.material import MaterialLoaderUtility
from blenderproc.python.types.MeshObjectUtility import convert_to_meshes
from blenderproc.python.utility.Utility import Utility, Config
from blenderproc.python.constructor.RandomRoomConstructor import construct_random_room


class RandomRoomConstructorModule(Module):
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
    "bed" and "chair". Checkout the `examples/datasets/ikea` if you want to know more on that particular dataset.

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

        self.used_floor_area = self.config.get_float("floor_area")
        self.amount_of_extrusions = self.config.get_int("amount_of_extrusions", 0)
        self.fac_from_square_room = self.config.get_float("fac_base_from_square_room", 0.3)
        self.corridor_width = self.config.get_float("minimum_corridor_width", 0.9)
        self.wall_height = self.config.get_float("wall_height", 2.5)
        self.amount_of_floor_cuts = self.config.get_int("amount_of_floor_cuts", 2)
        self.only_use_big_edges = self.config.get_bool("only_use_big_edges", True)
        self.create_ceiling = self.config.get_bool("create_ceiling", True)
        self.assign_material_to_ceiling = self.config.get_bool("assign_material_to_ceiling", False)
        self.tries_per_face = self.config.get_int("placement_tries_per_face", 3)
        self.amount_of_objects_per_sq_meter = self.config.get_float("amount_of_objects_per_sq_meter", 3.0)

    def run(self):
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

        # only select non see through materials
        config = {"conditions": {"cp_is_cc_texture": True, "cf_principled_bsdf_Alpha_eq": 1.0}}
        material_getter = MaterialProvider(Config(config))
        all_cc_materials = MaterialLoaderUtility.convert_to_materials(material_getter.run())

        construct_random_room(
            used_floor_area=self.used_floor_area,
            interior_objects=convert_to_meshes(loaded_objects),
            materials=all_cc_materials,
            amount_of_extrusions=self.amount_of_extrusions,
            fac_from_square_room=self.fac_from_square_room,
            corridor_width=self.corridor_width,
            wall_height=self.wall_height,
            amount_of_floor_cuts=self.amount_of_floor_cuts,
            only_use_big_edges=self.only_use_big_edges,
            create_ceiling=self.create_ceiling,
            assign_material_to_ceiling=self.assign_material_to_ceiling,
            placement_tries_per_face=self.tries_per_face,
            amount_of_objects_per_sq_meter=self.amount_of_objects_per_sq_meter
        )
