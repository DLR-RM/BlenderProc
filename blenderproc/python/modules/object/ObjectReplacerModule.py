from blenderproc.python.modules.main.Module import Module
from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes
from blenderproc.python.object.ObjectReplacer import replace_objects
from mathutils import Euler

class ObjectReplacerModule(Module):
    """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the
        objects to replace with, can be selected over Selectors (getter.Entity).

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - replace_ratio
          - Ratio of objects in the original scene, which will be replaced. Default: 1.
          - float
        * - copy_properties
          - Copies the custom properties of the objects_to_be_replaced to the objects_to_replace_with. Default:
            True.
          - bool
        * - objects_to_be_replaced
          - Provider (Getter): selects objects, which should be removed from the scene, gets list of objects
            following a certain condition. Default: [].
          - Provider
        * - objects_to_replace_with
          - Provider (Getter): selects objects, which will be tried to be added to the scene, gets list of objects
            following a certain condition. Default: [].
          - Provider
        * - ignore_collision_with
          - Provider (Getter): selects objects, which are not checked for collisions with. Default: [].
          - Provider
        * - max_tries
          - Maximum number of tries to replace one object. Default: 100.
          - int
        * - relative_rotation_sampler
          - Here call an appropriate Provider (Sampler) in order to sample a relative rotation to apply to the objects added to the scene.
            This random rotation is applied after the objects have been aligned to the objects they replace.
            If no relative_rotation_sampler is given, the object poses are no randomized. Default: None.
          - Provider
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Replaces mesh objects with another mesh objects and scales them accordingly, the replaced objects and the objects to replace with in following steps:
        1. Find which object to replace.
        2. Place the new object in place of the object to be replaced and scale accordingly.
        2. If there is no collision, between that object and the objects in the scene, then do replace and delete the original object.

        """

        if self.config.has_param("relative_rotation_sampler"):
            def relative_pose_sampler(obj):
                # Sample random rotation and apply it to the objects pose
                obj.blender_obj.rotation_euler.rotate(Euler(self.config.get_list("relative_rotation_sampler")))
        else:
            relative_pose_sampler = None

        replace_objects(
            objects_to_be_replaced=convert_to_meshes(self.config.get_list("objects_to_be_replaced", [])),
            objects_to_replace_with=convert_to_meshes(self.config.get_list("objects_to_replace_with", [])),
            ignore_collision_with=convert_to_meshes(self.config.get_list("ignore_collision_with", [])),
            replace_ratio=self.config.get_float("replace_ratio", 1),
            copy_properties=self.config.get_bool("copy_properties", True),
            max_tries=self.config.get_int("max_tries", 100),
            relative_pose_sampler=relative_pose_sampler
        )
