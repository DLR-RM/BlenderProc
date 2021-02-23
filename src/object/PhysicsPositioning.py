import bpy
import mathutils
import numpy as np

from src.main.Module import Module
from src.utility.BlenderUtility import get_all_blender_mesh_objects, get_bound_volume


class PhysicsPositioning(Module):
    """ Performs physics simulation in the scene, assigns new poses for all objects that participated.

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
            also make objects hover a bit. Default: 0.001.
          - float
        * - substeps_per_frame
          - Number of simulation steps taken per frame. Default: 10.
          - int
        * - solver_iters
          - Number of constraint solver iterations made per simulation step. Default: 10.
          - int
        * - collision_mesh_source
          - Source of the mesh used to create collision shape. Default: 'FINAL'. Available: 'BASE', 'DEFORM',
            'FINAL'.
          - string
        * - collision_shape
          - Collision shape of object in simulation. Default: 'CONVEX_HULL'. Available: 'BOX', 'SPHERE', 'CAPSULE',
            'CYLINDER', 'CONE', 'CONVEX_HULL', 'MESH'.
          - string
        * - objs_with_box_collision_shape
          - List of objects that get 'BOX' collision shape instead 'collision_shape'. Result of the getter.Entity.
            Default: []
          - list
        * - mass_scaling
          - Toggles scaling of mass for objects (1 kg/1m3 of a bounding box). Default: False.
          - bool
        * - mass_factor
          - Scaling factor for mass. Defines the linear function mass=bounding_box_volume*mass_factor (defines
            material density). Default: 1.
          - float
        * - friction
          - Resistance of object to movement. Default: 0.5. Range: [0, inf]
          - float
        * - angular_damping
          - Amount of angular velocity that is lost over time. Default: 0.1. Range: [0, 1]
          - float
        * - linear_damping
          - Amount of linear velocity that is lost over time. Default: 0.04. Range: [0, 1]
          - float
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.object_stopped_location_threshold = self.config.get_float("object_stopped_location_threshold", 0.01)
        self.object_stopped_rotation_threshold = self.config.get_float("object_stopped_rotation_threshold", 0.1)
        self.collision_margin = self.config.get_float("collision_margin", 0.001)
        self.collision_mesh_source = self.config.get_string('collision_mesh_source', 'FINAL')
        if config.has_param("steps_per_sec"):
            raise Exception("You are using the outdated parameter steps_per_sec. Please update your config by switching to substeps_per_frame (was changed in blender 2.91).")
        self.substeps_per_frame = self.config.get_int("substeps_per_frame", 10)
        self.solver_iters = self.config.get_int("solver_iters", 10)
        self.mass_scaling = self.config.get_bool("mass_scaling", False)
        self.mass_factor = self.config.get_float("mass_factor", 1)
        self.collision_shape = self.config.get_string("collision_shape", "CONVEX_HULL")
        self.friction = self.config.get_float("friction", 0.5)
        self.angular_damping = self.config.get_float("angular_damping",0.1)
        self.linear_damping = self.config.get_float("linear_damping",0.04)
        
    def run(self):
        """ Performs physics simulation in the scene. """
        # locations of all soon to be active objects before we shift their origin points
        locations_before_origin_shift = {}
        for obj in get_all_blender_mesh_objects():
            if obj["physics"]:
                locations_before_origin_shift.update({obj.name: obj.location.copy()})
        # enable rigid body and shift origin point for active objects
        locations_after_origin_shift = self._add_rigidbody()
        # compute origin point shift for all active objects
        origin_shift = {}
        for obj in locations_after_origin_shift:
            shift = locations_before_origin_shift[obj] - locations_after_origin_shift[obj]
            origin_shift.update({obj: shift})

        bpy.context.scene.rigidbody_world.substeps_per_frame = self.substeps_per_frame
        bpy.context.scene.rigidbody_world.solver_iterations = self.solver_iters

        obj_poses_before_sim = self._get_pose()
        # perform simulation
        obj_poses_after_sim = self._do_simulation()
        # reset origin point of all active objects to the total shift location of the 3D cursor
        for obj in get_all_blender_mesh_objects():
            if obj.rigid_body.type == "ACTIVE":
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                # compute relative object rotation before and after simulation
                R_obj_before_sim = mathutils.Euler(obj_poses_before_sim[obj.name]['rotation']).to_matrix()
                R_obj_after = mathutils.Euler(obj_poses_after_sim[obj.name]['rotation']).to_matrix()
                R_obj_rel = R_obj_before_sim @ R_obj_after.transposed()
                # compute origin shift in object coordinates
                origin_shift[obj.name] = R_obj_rel.transposed() @ origin_shift[obj.name]
                # set 3d cursor location to the total shift of the object
                bpy.context.scene.cursor.location = origin_shift[obj.name] + obj_poses_after_sim[obj.name]['location']
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                obj.select_set(False)

        # reset 3D cursor location
        bpy.context.scene.cursor.location = mathutils.Vector([0, 0, 0])

        # get current poses
        curr_pose = self._get_pose()
        # displace for the origin shift
        final_poses = {}
        for obj in curr_pose:
            final_poses.update({obj: {'location': curr_pose[obj]['location'] + origin_shift[obj], 'rotation': curr_pose[obj]['rotation']}})
        self._set_pose(final_poses)

        self._remove_rigidbody()

    def _add_rigidbody(self):
        """ Adds a rigidbody element to all mesh objects and sets their type depending on the custom property "physics".

        :return: Object locations after origin point shift. Type: dict.
        """
        locations_after_origin_shift = {}
        for obj in get_all_blender_mesh_objects():
            bpy.context.view_layer.objects.active = obj
            bpy.ops.rigidbody.object_add()
            if "physics" not in obj:
                raise Exception("The obj: '{}' has no physics attribute, each object needs one.".format(obj.name))
            obj.rigid_body.type = "ACTIVE" if obj["physics"] else "PASSIVE"
            obj.select_set(True)
            if obj in self.config.get_list("objs_with_box_collision_shape", []):
                obj.rigid_body.collision_shape = "BOX"
            else:
                obj.rigid_body.collision_shape = self.collision_shape
            obj.rigid_body.collision_margin = self.collision_margin
            obj.rigid_body.use_margin = True
            obj.rigid_body.mesh_source = self.collision_mesh_source
            obj.rigid_body.friction = self.friction
            obj.rigid_body.angular_damping = self.angular_damping
            obj.rigid_body.linear_damping = self.linear_damping
            if obj.rigid_body.type == "ACTIVE":
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                locations_after_origin_shift.update({obj.name: obj.location.copy()})

            if self.mass_scaling:
                obj.rigid_body.mass = get_bound_volume(obj) * self.mass_factor

            obj.select_set(False)

        return locations_after_origin_shift

    def _remove_rigidbody(self):
        """ Removes the rigidbody element from all mesh objects. """
        for obj in get_all_blender_mesh_objects():
            bpy.context.view_layer.objects.active = obj
            bpy.ops.rigidbody.object_remove()

    def _seconds_to_frames(self, seconds):
        """ Converts the given number of seconds into the corresponding number of blender animation frames.

        :param seconds: The number of seconds. Type: int.
        :return: The number of frames. Type: int.
        """
        return int(seconds * bpy.context.scene.render.fps)

    def _frames_to_seconds(self, frames):
        """ Converts the given number of frames into the corresponding number of seconds.

        :param frames: The number of frames. Type: int.
        :return: The number of seconds: Type: int.
        """
        return float(frames) / bpy.context.scene.render.fps

    def _do_simulation(self):
        """ Perform the simulation.

        This method bakes the simulation for the configured number of iterations and returns all object positions at the last frame.

        :return: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        """
        # Run simulation
        point_cache = bpy.context.scene.rigidbody_world.point_cache
        point_cache.frame_start = 1

        min_simulation_time = self.config.get_float("min_simulation_time", 4.0)
        max_simulation_time = self.config.get_float("max_simulation_time", 40.0)
        check_object_interval = self.config.get_float("check_object_interval", 2.0)

        if min_simulation_time >= max_simulation_time:
            raise Exception("max_simulation_iterations has to be bigger than min_simulation_iterations")

        # Run simulation starting from min to max in the configured steps
        for current_time in np.arange(min_simulation_time, max_simulation_time, check_object_interval):
            current_frame = self._seconds_to_frames(current_time)
            print("Running simulation up to " + str(current_time) + " seconds (" + str(current_frame) + " frames)")

            # Simulate current interval
            point_cache.frame_end = current_frame
            bpy.ops.ptcache.bake({"point_cache": point_cache}, bake=True)

            # Go to second last frame and get poses
            bpy.context.scene.frame_set(current_frame - self._seconds_to_frames(1))
            old_poses = self._get_pose()

            # Go to last frame of simulation and get poses
            bpy.context.scene.frame_set(current_frame)
            new_poses = self._get_pose()

            # Free bake (this will not completely remove the simulation cache, so further simulations can reuse the already calculated frames)
            bpy.ops.ptcache.free_bake({"point_cache": point_cache})

            # If objects have stopped moving between the last two frames, then stop here
            if self._have_objects_stopped_moving(old_poses, new_poses):
                print("Objects have stopped moving after " + str(current_time) + "  seconds (" + str(current_frame) + " frames)")
                break
            elif current_time + check_object_interval >= max_simulation_time:
                print("Stopping simulation as configured max_simulation_time has been reached")
        return new_poses

    def _get_pose(self):
        """Returns position and rotation values of all objects in the scene with ACTIVE rigid_body type.

        :return: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        """
        objects_poses = {}
        for obj in get_all_blender_mesh_objects():
            if obj.rigid_body.type == 'ACTIVE':
                location = bpy.context.scene.objects[obj.name].matrix_world.translation.copy()
                rotation = mathutils.Vector(bpy.context.scene.objects[obj.name].matrix_world.to_euler())
                objects_poses.update({obj.name: {'location': location, 'rotation': rotation}})

        return objects_poses

    def _set_pose(self, pose_dict):
        """ Sets location and rotation properties of objects.

        :param pose_dict: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        """
        for obj_name in pose_dict:
            bpy.context.scene.objects[obj_name].location = pose_dict[obj_name]['location']
            bpy.context.scene.objects[obj_name].rotation_euler = pose_dict[obj_name]['rotation']


    def _have_objects_stopped_moving(self, last_poses, new_poses):
        """ Check if the difference between the two given poses per object is smaller than the configured threshold.

        :param last_poses: Type: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        :param new_poses: Type: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        :return: True, if no objects are moving anymore.
        """
        stopped = True
        for obj_name in last_poses:
            # Check location difference
            location_diff = last_poses[obj_name]['location'] - new_poses[obj_name]['location']
            stopped = stopped and not any(location_diff[i] > self.object_stopped_location_threshold for i in range(3))

            # Check rotation difference
            rotation_diff = last_poses[obj_name]['rotation'] - new_poses[obj_name]['rotation']
            stopped = stopped and not any(rotation_diff[i] > self.object_stopped_rotation_threshold for i in range(3))

            if not stopped:
                break

        return stopped
