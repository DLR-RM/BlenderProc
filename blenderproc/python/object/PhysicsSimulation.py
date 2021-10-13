import bpy
import mathutils
import numpy as np

from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects
from blenderproc.python.types.MeshObjectUtility import disable_all_rigid_bodies, get_all_mesh_objects, MeshObject
from blenderproc.python.utility.Utility import Utility


def simulate_physics_and_fix_final_poses(min_simulation_time: float = 4.0, max_simulation_time: float = 40.0,
                                         check_object_interval: float = 2.0,
                                         object_stopped_location_threshold: float = 0.01,
                                         object_stopped_rotation_threshold: float = 0.1, substeps_per_frame: int = 10,
                                         solver_iters: int = 10):
    """ Simulates the current scene and in the end fixes the final poses of all active objects.

    The simulation is run for at least `min_simulation_time` seconds and at a maximum `max_simulation_time` seconds.
    Every `check_object_interval` seconds, it is checked if the maximum object movement in the last second is below a given threshold.
    If that is the case, the simulation is stopped.

    After performing the simulation, the simulation cache is removed, the rigid body components are disabled and the pose of the active objects is set to their final pose in the simulation.

    :param min_simulation_time: The minimum number of seconds to simulate.
    :param max_simulation_time: The maximum number of seconds to simulate.
    :param check_object_interval: The interval in seconds at which all objects should be checked if they are still moving. If all objects
                                  have stopped moving, than the simulation will be stopped.
    :param object_stopped_location_threshold: The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
                                              that an object is still recognized as 'stopped moving'.
    :param object_stopped_rotation_threshold: The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
                                              that an object is still recognized as 'stopped moving'.
    :param substeps_per_frame: Number of simulation steps taken per frame.
    :param solver_iters: Number of constraint solver iterations made per simulation step.
    """
    # Undo changes made in the simulation like origin adjustment and persisting the object's scale
    with Utility.UndoAfterExecution():
        # Run simulation and remember poses before and after
        obj_poses_before_sim = PhysicsSimulation._get_pose()
        origin_shifts = simulate_physics(min_simulation_time, max_simulation_time, check_object_interval,
                                         object_stopped_location_threshold, object_stopped_rotation_threshold,
                                         substeps_per_frame, solver_iters)
        obj_poses_after_sim = PhysicsSimulation._get_pose()

        # Make sure to remove the simulation cache as we are only interested in the final poses
        bpy.ops.ptcache.free_bake({"point_cache": bpy.context.scene.rigidbody_world.point_cache})

    # Fix the pose of all objects to their pose at the and of the simulation (also revert origin shift)
    for obj in get_all_mesh_objects():
        if obj.has_rigidbody_enabled():
            # Skip objects that have parents with compound rigid body component
            has_compound_parent = obj.get_parent() is not None and isinstance(obj.get_parent(), MeshObject) \
                                  and obj.get_parent().get_rigidbody() is not None \
                                  and obj.get_parent().get_rigidbody().collision_shape == "COMPOUND"
            if obj.get_rigidbody().type == "ACTIVE" and not has_compound_parent:
                # compute relative object rotation before and after simulation
                R_obj_before_sim = mathutils.Euler(obj_poses_before_sim[obj.get_name()]['rotation']).to_matrix()
                R_obj_after = mathutils.Euler(obj_poses_after_sim[obj.get_name()]['rotation']).to_matrix()
                R_obj_rel = R_obj_before_sim @ R_obj_after.transposed()
                # Apply relative rotation to origin shift
                origin_shift = R_obj_rel.transposed() @ mathutils.Vector(origin_shifts[obj.get_name()])

                # Fix pose of object to the one it had at the end of the simulation
                obj.set_location(obj_poses_after_sim[obj.get_name()]['location'] - origin_shift)
                obj.set_rotation_euler(obj_poses_after_sim[obj.get_name()]['rotation'])

    # Deactivate the simulation so it does not influence object positions
    bpy.context.scene.rigidbody_world.enabled = False
    bpy.context.view_layer.update()


def simulate_physics(min_simulation_time: float = 4.0, max_simulation_time: float = 40.0,
                     check_object_interval: float = 2.0, object_stopped_location_threshold: float = 0.01,
                     object_stopped_rotation_threshold: float = 0.1, substeps_per_frame: int = 10,
                     solver_iters: int = 10) -> dict:
    """ Simulates the current scene.

    The simulation is run for at least `min_simulation_time` seconds and at a maximum `max_simulation_time` seconds.
    Every `check_object_interval` seconds, it is checked if the maximum object movement in the last second is below a given threshold.
    If that is the case, the simulation is stopped.

    The origin of all objects is set to their center of mass in this function which is necessary to achieve a realistic simulation in blender (see https://blender.stackexchange.com/questions/167488/physics-not-working-as-expected)
    Also the scale of each participating object is persisted as scale != 1 can make the simulation unstable.

    :param min_simulation_time: The minimum number of seconds to simulate.
    :param max_simulation_time: The maximum number of seconds to simulate.
    :param check_object_interval: The interval in seconds at which all objects should be checked if they are still moving. If all objects
                                  have stopped moving, than the simulation will be stopped.
    :param object_stopped_location_threshold: The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
                                              that an object is still recognized as 'stopped moving'.
    :param object_stopped_rotation_threshold: The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
                                              that an object is still recognized as 'stopped moving'.
    :param substeps_per_frame: Number of simulation steps taken per frame.
    :param solver_iters: Number of constraint solver iterations made per simulation step.
    :return: A dict containing for every active object the shift that was added to their origins.
    """
    # Shift the origin of all objects to their center of mass to make the simulation more realistic
    origin_shift = {}
    for obj in get_all_mesh_objects():
        if obj.has_rigidbody_enabled():
            prev_origin = obj.get_origin()
            new_origin = obj.set_origin(mode="CENTER_OF_VOLUME")
            origin_shift[obj.get_name()] = new_origin - prev_origin

            # Persist mesh scaling as having a scale != 1 can make the simulation unstable
            obj.persist_transformation_into_mesh(location=False, rotation=False, scale=True)

    # Configure simulator
    bpy.context.scene.rigidbody_world.substeps_per_frame = substeps_per_frame
    bpy.context.scene.rigidbody_world.solver_iterations = solver_iters

    # Perform simulation
    PhysicsSimulation._do_simulation(min_simulation_time, max_simulation_time, check_object_interval,
                                     object_stopped_location_threshold, object_stopped_rotation_threshold)

    return origin_shift


class PhysicsSimulation:

    @staticmethod
    def _seconds_to_frames(seconds: float) -> int:
        """ Converts the given number of seconds into the corresponding number of blender animation frames.

        :param seconds: The number of seconds.
        :return: The number of frames.
        """
        return int(seconds * bpy.context.scene.render.fps)

    @staticmethod
    def _frames_to_seconds(frames: int) -> float:
        """ Converts the given number of frames into the corresponding number of seconds.

        :param frames: The number of frames.
        :return: The number of seconds:
        """
        return float(frames) / bpy.context.scene.render.fps

    @staticmethod
    def _do_simulation(min_simulation_time: float, max_simulation_time: float, check_object_interval: float,
                       object_stopped_location_threshold: float, object_stopped_rotation_threshold: float):
        """ Perform the simulation.

        This method bakes the simulation for the configured number of iterations and returns all object positions at the last frame.
        :param min_simulation_time: The minimum number of seconds to simulate.
        :param max_simulation_time: The maximum number of seconds to simulate.
        :param check_object_interval: The interval in seconds at which all objects should be checked if they are still moving. If all objects
                                      have stopped moving, than the simulation will be stopped.
        :param object_stopped_location_threshold: The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
                                                  that an object is still recognized as 'stopped moving'.
        :param object_stopped_rotation_threshold: The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
                                                  that an object is still recognized as 'stopped moving'.
        """
        # Make sure the RigidBody world is active
        bpy.context.scene.rigidbody_world.enabled = True

        # Run simulation
        point_cache = bpy.context.scene.rigidbody_world.point_cache
        point_cache.frame_start = 1

        if min_simulation_time >= max_simulation_time:
            raise Exception("max_simulation_iterations has to be bigger than min_simulation_iterations")

        # Run simulation starting from min to max in the configured steps
        for current_time in np.arange(min_simulation_time, max_simulation_time, check_object_interval):
            current_frame = PhysicsSimulation._seconds_to_frames(current_time)
            print("Running simulation up to " + str(current_time) + " seconds (" + str(current_frame) + " frames)")

            # Simulate current interval
            point_cache.frame_end = current_frame
            bpy.ops.ptcache.bake({"point_cache": point_cache}, bake=True)

            # Go to second last frame and get poses
            bpy.context.scene.frame_set(current_frame - PhysicsSimulation._seconds_to_frames(1))
            old_poses = PhysicsSimulation._get_pose()

            # Go to last frame of simulation and get poses
            bpy.context.scene.frame_set(current_frame)
            new_poses = PhysicsSimulation._get_pose()

            # If objects have stopped moving between the last two frames, then stop here
            if PhysicsSimulation._have_objects_stopped_moving(old_poses, new_poses, object_stopped_location_threshold,
                                                              object_stopped_rotation_threshold):
                print("Objects have stopped moving after " + str(current_time) + "  seconds (" + str(
                    current_frame) + " frames)")
                break
            elif current_time + check_object_interval >= max_simulation_time:
                print("Stopping simulation as configured max_simulation_time has been reached")
            else:
                # Free bake (this will not completely remove the simulation cache, so further simulations can reuse the already calculated frames)
                bpy.ops.ptcache.free_bake({"point_cache": point_cache})

    @staticmethod
    def _get_pose() -> dict:
        """ Returns position and rotation values of all objects in the scene with ACTIVE rigid_body type.

        :return: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        """
        objects_poses = {}
        objects_with_physics = [obj for obj in get_all_blender_mesh_objects() if obj.rigid_body is not None]

        for obj in objects_with_physics:
            if obj.rigid_body.type == 'ACTIVE':
                location = bpy.context.scene.objects[obj.name].matrix_world.translation.copy()
                rotation = mathutils.Vector(bpy.context.scene.objects[obj.name].matrix_world.to_euler())
                objects_poses.update({obj.name: {'location': location, 'rotation': rotation}})

        return objects_poses

    @staticmethod
    def _have_objects_stopped_moving(last_poses: dict, new_poses: dict, object_stopped_location_threshold: float,
                                     object_stopped_rotation_threshold: float) -> bool:
        """ Check if the difference between the two given poses per object is smaller than the configured threshold.

        :param last_poses: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        :param new_poses: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        :param object_stopped_location_threshold: The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
                                                  that an object is still recognized as 'stopped moving'.
        :param object_stopped_rotation_threshold: The maximum difference per second and per coordinate in the rotation Euler vector that is allowed. such
                                                  that an object is still recognized as 'stopped moving'.
        :return: True, if no objects are moving anymore.
        """
        stopped = True
        for obj_name in last_poses:
            # Check location difference
            location_diff = last_poses[obj_name]['location'] - new_poses[obj_name]['location']
            stopped = stopped and not any(location_diff[i] > object_stopped_location_threshold for i in range(3))

            # Check rotation difference
            rotation_diff = last_poses[obj_name]['rotation'] - new_poses[obj_name]['rotation']
            stopped = stopped and not any(rotation_diff[i] > object_stopped_rotation_threshold for i in range(3))

            if not stopped:
                break

        return stopped
