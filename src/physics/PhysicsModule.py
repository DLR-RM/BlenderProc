import mathutils
import bpy

from src.main.Module import Module

class PhysicsModule(Module):
    """ Performs physics simulation in the scene, assigns new poses for all objects that participated.

    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.objects = bpy.context.scene.objects

    def run(self):
    """ Performs physics simulation in the scene. """
        # Some frame number where we will check if moving has stopped
        animation_end_frame = 100
        # Select all objects
        _select_all_objects(True)
        # Enable rigid_body property
        bpy.ops.rigidbody.object_add()
        # deselect all objects
        _select_all_objects(False)
        # Set rigid_body type ofr all objects in accordance to their custom 'physics' property
        _set_rigidbody_state()
        # Get starting poses of all objects
        start_pose = _get_pose()
        # check for displacement value or if motion stopped altogether
            # Set frame
            bpy.context.scene.frame_set(animation_end_frame)
            # Get poses for current frame
            end_location = _get_pose()
            # Ged displacement
            displacement = _get_displacement()
            # New frame
            animation_end_frame += 10
        # Set all objects to PASSIVE rigid_body type
        _reset_rigidbody_state()
        # Maybe disable rigid_body property here idk really who know i do not
        # Assign final poses to objects
        _set_pose(end_pose)

    def _set_rigidbody_state(self):
        """Sets the rigid_body type according to the preconfigured custom property of the object."""
        obj.rigid_body.type = x["physics"] for obj in self.objects

    def _reset_rigidbody_state(self):
        """Sets the rigid_body type to PASSIVE for all objects in the scene."""
        obj.rigid_body.type = 'PASSIVE' for obj in self.objects

    def _get_pose(self):
        """Returns position and rotation values of all objects in the scene with ACTIVE rigid_body type.
        
        :return: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}. 
        """ 
        objects_poses = {}
        for obj in self.objects:
            if obj.rigid_body.type == 'ACTIVE':
                location = bpy.context.scene.objects[obj.name].matrix_world.translation
                rotation = bpy.context.scene.objects[obj.name].matrix_world.to_euler()
                objects_poses.update({obj.name : {'location': location, 'rotation': rotation}})
    
    return objects_poses

    def _select_all_objects(self, mode):
        """ Sets select mode of all objects in the scene.

        :param mode: Boolean that specifies if objects are to be selecter or deselected. True - select, False - deselect.
        """
        obj.select_set(mode) for obj in self.objects

    def _set_pose(self, pose_dict):
        """ Sets location and rotation properties of  objects.

        :param pose_dict: Dict of form {obj_name:{'location':[x, y, z], 'rotation':[x_rot, y_rot, z_rot]}}. 
        """
        for obj_name in pose_dict:
            bpy.context.scene.objects[obj_name].location = pose_dict[obj_name]['location']
            bpy.context.scene.objects[obj_name].rotation = pose_dict[obj_name]['rotation']

    def _get_displacement():
        """
        """
        pass


        
