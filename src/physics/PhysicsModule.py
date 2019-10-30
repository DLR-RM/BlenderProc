import mathutils
import bpy

from src.main.Module import Module

class PhysicsModule(Module):
    """

    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.objects = bpy.context.scene.objects

    def run(self):
        animation_end_frame = 100
        _select_all_objects(True)
        bpy.ops.rigidbody.object_add()
        _select_all_objects(False)
        _set_rigidbody_state()
        start_pose = _get_pose()
        while
            bpy.context.scene.frame_set(animation_end_frame)
            end_location = _get_pose()
            displacement = _get_displacement()
            animation_end_frame += 10
        _reset_rigidbody_state()
        _set_pose(end_pose)

    def _set_rigidbody_state(self):
        """
        """
        obj.rigid_body.type = x["physics"] for obj in self.objects

    def _reset_rigidbody_state(self):
        """
        """
        obj.rigid_body.type = 'PASSIVE' for obj in self.objects

    def _get_pose(self):
        objects_poses = {}
        for obj in self.objects:
            if obj.rigid_body.type == 'ACTIVE':
                location = bpy.context.scene.objects[obj.name].matrix_world.translation
                rotation = bpy.context.scene.objects[obj.name].matrix_world.to_euler()
                objects_poses.update({obj.name : {'location': location, 'rotation': rotation}})
    
    return objects_poses

    def _select_all_objects(self, mode):
        """
        """
        obj.select_set(mode) for obj in self.objects

    def _set_pose(self, pose_dict):
        """
        """
        for obj_name in pose_dict:
            bpy.context.scene.objects[obj_name].location = pose_dict[obj_name]['location']
            bpy.context.scene.objects[obj_name].rotation = pose_dict[obj_name]['rotation']

    def _get_displacement():
        """
        """



        
