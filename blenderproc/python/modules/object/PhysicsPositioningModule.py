from blenderproc.python.modules.main.Module import Module
from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.object.PhysicsSimulation import simulate_physics_and_fix_final_poses


class PhysicsPositioningModule(Module):
    """ Performs physics simulation in the scene, assigns new poses for all objects that participated.

    It is possible to set object-specific physics attributes via its custom properties:
    - physics_mass
    - physics_collision_shape
    - physics_collision_margin
    - physics_collision_mesh_source
    - physics_friction
    - physics_angular_damping
    - physics_linear_damping

    If an attribute for an object is not set via the custom properties, then the corresponding default value from this module's configuration is used.
    See the following table for detailed descriptions about each physics attribute.

    **Configuration**:

    .. list-table::
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - object_stopped_location_threshold
          - The maximum difference per second and per coordinate in the location vector that is allowed, such that
            an object is still recognized as 'stopped moving'. Default: 0.01
          - float
        * - object_stopped_rotation_threshold
          - The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
            that an object is still recognized as 'stopped moving'. Default: 0.1
          - float
        * - min_simulation_time
          - The minimum number of seconds to simulate. Default: 4.0
          - float
        * - check_object_interval
          - The interval in seconds at which all objects should be checked if they are still moving. If all objects
            have stopped moving, than the simulation will be stopped. Default: 2.0
          - float
        * - max_simulation_time
          - The maximum number of seconds to simulate. Default: 40.0
          - int
        * - collision_margin
          - The margin around objects where collisions are already recognized. Higher values improve stability, but
            also make objects hover a bit. This value is used if for an object no custom property `physics_collision_margin` is set. Default: 0.001.
          - float
        * - substeps_per_frame
          - Number of simulation steps taken per frame. Default: 10.
          - int
        * - solver_iters
          - Number of constraint solver iterations made per simulation step. Default: 10.
          - int
        * - collision_mesh_source
          - Source of the mesh used to create collision shape. This value is used if for an object no custom property `physics_collision_mesh_source` is set.
            Default: 'FINAL'. Available: 'BASE', 'DEFORM', 'FINAL'.
          - string
        * - collision_shape
          - Collision shape of object in simulation. This value is used if for an object no custom property `physics_collision_shape` is set.
            If 'CONVEX_DECOMPOSITION' is chosen, the object is automatically decomposed using the V-HACD library.
            Default: 'CONVEX_HULL'. Available: 'BOX', 'SPHERE', 'CAPSULE', 'CYLINDER', 'CONE', 'CONVEX_HULL', 'MESH', 'CONVEX_DECOMPOSITION'.
          - string
        * - mass_scaling
          - Toggles scaling of mass for objects (1 kg/1m3 of a bounding box). Default: False.
          - bool
        * - mass_factor
          - Scaling factor for mass. Defines the linear function mass=bounding_box_volume*mass_factor (defines
            material density). Default: 1.
          - float
        * - friction
          - Resistance of object to movement. This value is used if for an object no custom property `physics_friction` is set.
            Default: 0.5. Range: [0, inf]
          - float
        * - angular_damping
          - Amount of angular velocity that is lost over time. This value is used if for an object no custom property `physics_angular_damping` is set.
            Default: 0.1. Range: [0, 1]
          - float
        * - linear_damping
          - Amount of linear velocity that is lost over time. This value is used if for an object no custom property `physics_linear_damping` is set.
            Default: 0.04. Range: [0, 1]
          - float
        * - convex_decomposition_cache_path
          - If a directory is given, convex decompositions are stored there named after the meshes hash. If the same mesh is decomposed a second time, the result is loaded from the cache and the actual decomposition is skipped.
            Default: "blenderproc_resources/decomposition_cache"
          - string
        * - vhacd_path
          - The directory in which vhacd should be installed or is already installed.
            Default: "blenderproc_resources/vhacd"
          - string
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.collision_margin = self.config.get_float("collision_margin", 0.001)
        self.collision_mesh_source = self.config.get_string('collision_mesh_source', 'FINAL')
        if config.has_param("steps_per_sec"):
            raise Exception("You are using the outdated parameter steps_per_sec. Please update your config by switching to substeps_per_frame (was changed in blender 2.91).")
        self.mass_scaling = self.config.get_bool("mass_scaling", False)
        self.mass_factor = self.config.get_float("mass_factor", 1)
        self.collision_shape = self.config.get_string("collision_shape", "CONVEX_HULL")
        self.friction = self.config.get_float("friction", 0.5)
        self.angular_damping = self.config.get_float("angular_damping", 0.1)
        self.linear_damping = self.config.get_float("linear_damping", 0.04)
        self.convex_decomposition_cache_path = self.config.get_string("convex_decomposition_cache_path", "blenderproc_resources/decomposition_cache")
        self.vhacd_path = self.config.get_string("vhacd_path", "blenderproc_resources/vhacd")

    def run(self):
        """ Performs physics simulation in the scene. """
        self._add_rigidbody()
        simulate_physics_and_fix_final_poses(
            min_simulation_time=self.config.get_float("min_simulation_time", 4.0),
            max_simulation_time=self.config.get_float("max_simulation_time", 40.0),
            check_object_interval=self.config.get_float("check_object_interval", 2.0),
            object_stopped_location_threshold=self.config.get_float("object_stopped_location_threshold", 0.01),
            object_stopped_rotation_threshold=self.config.get_float("object_stopped_rotation_threshold", 0.1),
            substeps_per_frame=self.config.get_int("substeps_per_frame", 10),
            solver_iters=self.config.get_int("solver_iters", 10)
        )

    def _add_rigidbody(self):
        """ Adds a rigidbody element to all mesh objects and sets their physics attributes depending on their custom properties """

        # Temporary function which returns either the value set in the custom properties (if set) or the fallback value.
        def get_physics_attribute(obj, cp_name, default_value):
            if cp_name in obj:
                return obj[cp_name]
            else:
                return default_value

        # Go over all mesh objects and set their physics attributes based on the custom properties or (if not set) based on the module config
        for obj in get_all_blender_mesh_objects():
            mesh_obj = MeshObject(obj)
            # Skip if the object has already an active rigid body component
            if mesh_obj.get_rigidbody() is None:
                if "physics" not in obj:
                    raise Exception("The obj: '{}' has no physics attribute, each object needs one.".format(obj.name))

                # Collect physics attributes
                collision_shape = get_physics_attribute(obj, "physics_collision_shape", self.collision_shape)
                collision_margin = get_physics_attribute(obj, "physics_collision_margin", self.collision_margin)
                mass = get_physics_attribute(obj, "physics_mass", None if self.mass_scaling else 1)
                collision_mesh_source = get_physics_attribute(obj, "physics_collision_mesh_source", self.collision_mesh_source)
                friction = get_physics_attribute(obj, "physics_friction", self.friction)
                angular_damping = get_physics_attribute(obj, "physics_angular_damping", self.angular_damping)
                linear_damping = get_physics_attribute(obj, "physics_linear_damping", self.linear_damping)

                # Set physics attributes
                mesh_obj.enable_rigidbody(
                    active=obj["physics"],
                    collision_shape="COMPOUND" if collision_shape == "CONVEX_DECOMPOSITION" else collision_shape,
                    collision_margin=collision_margin,
                    mass=mass,
                    mass_factor=self.mass_factor,
                    collision_mesh_source=collision_mesh_source,
                    friction=friction,
                    angular_damping=angular_damping,
                    linear_damping=linear_damping
                )

                # Check if object needs decomposition
                if collision_shape == "CONVEX_DECOMPOSITION":
                    mesh_obj.build_convex_decomposition_collision_shape(self.vhacd_path, self._temp_dir, self.convex_decomposition_cache_path)

