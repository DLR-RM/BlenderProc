from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects
from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes, compute_poi


class POI(Provider):
    """
    Computes a point of interest in the scene. Point is defined as a location of the one of the selected objects
    that is the closest one to the mean location of the bboxes of the selected objects.

    Example 1: Return a location of the object that is the closest one to the mean bbox location of all MESH objects.

    .. code-block:: yaml

        {
          "provider": "getter.POI"
        }

    Example 2: Return a location of the object that is the closest one to the mean bbox location of MESH objects
    that have their custom property set to True.

    .. code-block:: yaml

        {
          "provider": "getter.POI",
          "selector": {
            "provider": "getter.Entity",
            "conditions": {
              "cp_shape_net_object": True,
              "type": "MESH"
            }
          }
        }

    **Configuration**:

    .. list-table::
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - selector
          - Objects to take part in the POI computation. Default: all mesh objects.
          - Provider
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Point of interest in the scene. Type: mathutils.Vector.
        """
        # For every selected object in the scene
        selected_objects = convert_to_meshes(self.config.get_list("selector", get_all_blender_mesh_objects()))
        if len(selected_objects) == 0:
            raise Exception("No objects were selected!")

        return compute_poi(selected_objects)
