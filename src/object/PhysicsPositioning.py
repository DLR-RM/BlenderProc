import mathutils
import bpy

from src.utility.BlenderUtility import get_all_mesh_objects, get_bound_volume
from src.main.Module import Module
import numpy as np

class PhysicsPositioning(Module):
    """ Performs physics simulation in the scene, assigns new poses for all objects that participated.

    .. csv-table::
       :header: "Parameter", "Description"

       "object_stopped_location_threshold", "The maximum difference per second and per coordinate in the location vector that is allowed, such that an object is still recognized as 'stopped moving'."
       "object_stopped_rotation_threshold", "The maximum difference per second and per coordinate in the rotation euler vector that is allowed. such that an object is still recognized as 'stopped moving'."
       "min_simulation_time", "The minimum number of seconds to simulate."
       "check_object_interval", "The interval in seconds at which all objects should be checked if they are still moving. If all objects have stopped moving, than the simulation will be stopped."
       "max_simulation_time", "The maximum number of seconds to simulate."
       "collision_margin", "The margin around objects where collisions are already recognized. Higher values improve stability, but also make objects hover a bit."
       "step_per_sec", "Number of simulation steps taken per second. Type: int. Optional. Default value: 60."
       "solver_iters", "Number of constraint solver iterations made per simulation step. Type: int. Optional. Default value: 10."
       "collision_mesh_source", "Source of the mesh used to create collision shape. Optional. Type: string. Default value: 'FINAL'. Available values: 'BASE', 'DEFORM', 'FINAL'."
       "mass_scaling", "Toggles scaling of mass for objects (1 kg/1m3 of a bounding box). Optional. Type: boolean. Default value: False."
       "mass_factor", "Scaling factor for mass. Defines the linear function mass=bounding_box_volume*mass_factor (defines material density). Optional. Type: float. Default value: 1."
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.object_stopped_location_threshold = self.config.get_float("object_stopped_location_threshold", 0.01)
        self.object_stopped_rotation_threshold = self.config.get_float("object_stopped_rotation_threshold", 0.1)
        self.collision_margin = self.config.get_float("collision_margin", 0.001)
        self.collision_mesh_source = self.config.get_string('collision_mesh_source', 'FINAL')
        self.steps_per_sec = self.config.get_int("steps_per_sec", 60)
        self.solver_iters = self.config.get_int("solver_iters", 10)
        self.mass_scaling = self.config.get_bool("mass_scaling", False)
        self.mass_factor = self.config.get_float("mass_factor", 1)

    def run(self):
        """ Performs physics simulation in the scene. """
        # Enable physics for all objects
        self._add_rigidbody()
        bpy.context.scene.rigidbody_world.steps_per_second = self.steps_per_sec
        bpy.context.scene.rigidbody_world.solver_iterations = self.solver_iters
        # Run simulation and use the position of the objects at the end of the simulation as new initial position.
        obj_poses = self._do_simulation()
        self._set_pose(obj_poses)

        # Disable physics for all objects
        self._remove_rigidbody()

    def _add_rigidbody(self):
        """ Adds a rigidbody element to all mesh objects and sets their type depending on the custom property "physics". """
        for obj in get_all_mesh_objects():
            bpy.context.view_layer.objects.active = obj
            bpy.ops.rigidbody.object_add()
            obj.rigid_body.type = "ACTIVE" if obj["physics"] else "PASSIVE"
            obj.rigid_body.collision_shape = "MESH"
            obj.rigid_body.collision_margin = self.collision_margin
            obj.rigid_body.mesh_source = self.collision_mesh_source
            if self.mass_scaling:
                obj.rigid_body.mass = get_bound_volume(obj) * self.mass_factor

    def _remove_rigidbody(self):
        """ Removes the rigidbody element from all mesh objects. """
        for obj in get_all_mesh_objects():
            bpy.context.view_layer.objects.active = obj
            bpy.ops.rigidbody.object_remove()

    def _seconds_to_frames(self, seconds):
        """ Converts the given number of seconds into the corresponding number of blender animation frames.

        :param seconds: The number of seconds
        :return: The number of frames
        """
        return int(seconds * bpy.context.scene.render.fps)

    def _frames_to_seconds(self, frames):
        """ Converts the given number of frames into the corresponding number of seconds.

        :param frames: The number of frames
        :return: The number of seconds
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
        for obj in get_all_mesh_objects():
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

        :param last_poses: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        :param new_poses: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
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
