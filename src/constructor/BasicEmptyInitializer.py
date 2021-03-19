import bpy

from src.main.Module import Module
from src.utility.Config import Config


class BasicEmptyInitializer(Module):
    """
    Adds/initializes basic empty objects in the scene. Allows setting the basic attribute values. For more precise
    and powerful object manipulation use manipulators.EntityManipulator module.

    These empty objects can be used to save locations or the be a focus point for the camera. They do not have any mesh
    data nor do the have any materials.

    Example 1: Add a empty axis to the scene.

    .. code-block:: yaml

        {
          "module": "constructor.BasicEmptyInitializer",
          "config": {
            "empties_to_add": [
            {
              "type": "plane_axes",
              "name": "Plan Axes"
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
        * - empties_to_add
          - List that contains entities configuration data in each cell. See table below for available parameters per
            cell. 
          - list

    **empties_to_add cell configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - type
          - Type of empty object to add. Available types: 'plain_axes'
          - string
        * - name
          - Name of the empty object.
          - string
        * - location
          - Location of the empty object. Default: [0, 0, 0].
          - mathutils.Vector
        * - rotation
          - Rotation (3 Euler angles) of the empty object. Default: [0, 0, 0].
          - mathutils.Vector
        * - scale
          - Scale of the empty object. Default: [1, 1, 1].
          - mathutils.Vector
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Adds specified basic empty objects to the scene and sets at least their names to the user-defined ones.
            1. Get configuration parameters' values.
            2. Add an object.
            3. Set attribute values.
        """
        empties_to_add = self.config.get_list("empties_to_add")
        for empty in empties_to_add:
            empty_conf = Config(empty)
            obj_type = empty_conf.get_string("type")
            obj_name = empty_conf.get_string("name")
            obj_location = empty_conf.get_vector3d("location", [0, 0, 0])
            obj_rotation = empty_conf.get_vector3d("rotation", [0, 0, 0])
            obj_scale = empty_conf.get_vector3d("scale", [1, 1, 1])
            new_obj = self._add_obj(obj_type)
            self._set_attrs(new_obj, obj_name, obj_location, obj_rotation, obj_scale)

    def _add_obj(self, obj_type):
        """ Adds an object to the scene.

        :param obj_type: Type of the object to add. Type: string.
        :return: Added object. Type: bpy.types.Object.
        """
        if obj_type == "plane_axes":
            bpy.ops.object.empty_add(type='PLAIN_AXES', align="WORLD")
        else:
            raise RuntimeError(f'Unknown basic empty type "{obj_type}"! Available types: "plane_axes".')

        new_obj = bpy.context.object
        return new_obj

    def _set_attrs(self, new_obj, obj_name, obj_location, obj_rotation, obj_scale):
        """ Sets the attribute values of the added object.

        :param new_obj: New object to modify. Type: bpy.types.Object.
        :param obj_name: Name of the object. Type: string.
        :param obj_location: XYZ location of the object. Type: mathutils.Vector.
        :param obj_rotation: Rotation (3 Euler angles) of the object. Type: mathutils.Vector.
        :param obj_scale: Scale of the object. Type: mathutils.Vector.
        """
        new_obj.name = obj_name
        new_obj.location = obj_location
        new_obj.rotation_euler = obj_rotation
        new_obj.scale = obj_scale
