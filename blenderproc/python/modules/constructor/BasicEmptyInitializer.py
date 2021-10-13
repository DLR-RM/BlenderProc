from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.types.EntityUtility import create_empty


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
              "type": "plain_axes",
              "name": "Plain Axes"
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
          - Type of empty object to add. Default: "plain_axes". Available types: ["plain_axes", "arrows", \
            "single_arrow", "circle", "cube", "sphere", "cone"]
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
            obj_name = empty_conf.get_string("name")
            obj_type = empty_conf.get_string("type", "plain_axes")

            entity = create_empty(obj_name, obj_type)
            entity.set_location(empty_conf.get_vector3d("location", [0, 0, 0]))
            entity.set_rotation_euler(empty_conf.get_vector3d("rotation", [0, 0, 0]))
            entity.set_scale(empty_conf.get_vector3d("scale", [1, 1, 1]))
