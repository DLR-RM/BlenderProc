import mathutils
import bpy

from src.main.Module import Module


class PhysicsPositioning(Module):
    """ Performs physics simulation in the scene, assigns new poses for all objects that participated.

    .. csv-table::
       :header: "Parameter", "Description"

       "simulation_iterations", "For how many iterations the simulation should be computed until the new object positions should be read."
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Performs physics simulation in the scene. """

        # Enable physics for all objects
        self._add_rigidbody()

        # Run simulation and use the position of the objects at the end of the simulation as new initial position.
        obj_poses = self._do_simulation()
        self._set_pose(obj_poses)

        # Disable physics for all objects
        self._remove_rigidbody()

    def _add_rigidbody(self):
        """ Adds a rigidbody element to all mesh objects and sets their type depending on the custom property "physics". """
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                bpy.ops.rigidbody.object_add()
                obj.rigid_body.type = obj["physics"]
                # TODO: Configure this per object. MESH is very slow but sometimes necessary.
                obj.rigid_body.collision_shape = "MESH"

    def _remove_rigidbody(self):
        """ Removes the rigidbody element from all mesh objects. """
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                bpy.ops.rigidbody.object_remove()

    def _do_simulation(self):
        """ Perform the simulation.

        This method bakes the simulation for the configured number of iterations and returns all object positions at the last frame.

        :return: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        """
        # Run simulation
        point_cache = bpy.context.scene.rigidbody_world.point_cache
        point_cache.frame_start = 1
        point_cache.frame_end = self.config.get_int("simulation_iterations")
        bpy.ops.ptcache.bake({"point_cache": point_cache}, bake=True)

        # Go to end of simulation
        bpy.context.scene.frame_set(self.config.get_int("simulation_iterations"))

        # Get poses of all objects
        obj_poses = self._get_pose()

        # Remove simulation cache
        bpy.ops.ptcache.free_bake({"point_cache": point_cache})

        return obj_poses

    def _get_pose(self):
        """Returns position and rotation values of all objects in the scene with ACTIVE rigid_body type.

        :return: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        """
        objects_poses = {}
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.rigid_body.type == 'ACTIVE':
                location = bpy.context.scene.objects[obj.name].matrix_world.translation
                rotation = bpy.context.scene.objects[obj.name].matrix_world.to_euler()
                objects_poses.update({obj.name: {'location': location, 'rotation': rotation}})

        return objects_poses

    def _set_pose(self, pose_dict):
        """ Sets location and rotation properties of objects.

        :param pose_dict: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}.
        """
        for obj_name in pose_dict:
            bpy.context.scene.objects[obj_name].location = pose_dict[obj_name]['location']
            bpy.context.scene.objects[obj_name].rotation_euler = pose_dict[obj_name]['rotation']

