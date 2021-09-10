import warnings
from math import radians

from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.object.FloorExtractor import extract_floor


class FloorExtractorModule(Module):
    """
    Will search for the specified object and splits the surfaces which point upwards at a specified level away

    Example 1, in which no height_list_path is set, here the floor is extracted automatically. By finding the group
    of polygons with the lowest median in Z direction.

    .. code-block:: yaml

        {
          "module": "object.FloorExtractor",
          "config": {
            "selector": {  # this will select the object, which gets splitt up
              "provider": "getter.Entity",
              "conditions": {
                "name": "wall"
              }
            },
            "compare_angle_degrees" : 7.5,  # this is the maximum angle in degree, in which the face can be twisted
            "compare_height": 0.15,  # the compare height is used after finding the floor
          }
        }

    Example 2, here the ceiling is extracted and not the floor. This is done by using the `up_vector_upwards` key,
    which is set to False here, so the polygons have to face in `[0, 0, -1]` direction. This will also flip, the search
    mechanism, now the highest group of polygons are used, not the lowest.

    .. code-block:: yaml

        {
          "module": "object.FloorExtractor",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": "wall"  # the wall object here contains the ceiling
              }
            },
            "up_vector_upwards": False,  # the polygons are now facing downwards: [0, 0, -1]
            "compare_angle_degrees" : 7.5,
            "compare_height": 0.15,
            "name_for_split_obj": "Ceiling"  # this is the new name of the object
          }
        }

    Example 3, if you are using this to extract the floor of replica scenes, to place objects on top of them.

    .. code-block:: yaml

        {
          "module": "object.FloorExtractor",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": "mesh"  # the wall object here contains the ceiling
              }
            },
            "compare_angle_degrees" : 7.5,
            "compare_height": 0.15,
            "name_for_split_obj": "floor"
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
          - Objects to where all polygons will be extracted.
          - Provider
        * - compare_angle_degrees
          - Maximum difference between the up vector and the current polygon normal in degrees. Default: 7.5.
          - float
        * - compare_height
          - Maximum difference in Z direction between the polygons median point and the specified height of the
            room. Default: 0.15.
          - float
        * - height_list_path
          - Path to a file with height values. If none is provided, a ceiling and floor is automatically detected. \
            This might fail. The height_list_values can be specified in a list like fashion in the file: [0.0, 2.0]. \
            These values are in the same size the dataset is in, which is usually meters. The content must always be \
            a list, e.g. [0.0].
          - string
        * - name_for_split_obj
          - Name for the newly created object, which faces fulfill the given parameters. Default: "Floor".
          - string
        * - up_vector_upwards
          - If this is True the `up_vec` points upwards -> [0, 0, 1] if not it points downwards: [0, 0, -1] in world \
            coordinates. This vector is used for the `compare_angle_degrees` option. Default: True.
          - bool
        * - add_properties
          - With `add_properties` it is possible to set custom properties for the newly separated objects. Use `cp_` \
            prefix for keys.
          - dict
        * - should_skip_if_object_is_already_there
          - If this is true no extraction will be done, if an object is there, which has the same name as
            name_for_split_obj, which would be used for the newly created object. Default: False.
          - bool
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Extracts floors in the following steps:
        1. Searchs for the specified object.
        2. Splits the surfaces which point upwards at a specified level away.
        """

        mesh_objects = []
        for obj in self.config.get_list("selector"):
            if obj.type != "MESH":
                warnings.warn("The object: {} is not a mesh but was selected in the FloorExtractor!".format(obj.name))
                continue
            mesh_objects.append(MeshObject(obj))

        floors = extract_floor(
            mesh_objects=mesh_objects,
            compare_angle_degrees=radians(self.config.get_float('compare_angle_degrees', 7.5)),
            compare_height=self.config.get_float('compare_height', 0.15),
            new_name_for_object=self.config.get_string("name_for_split_obj", "Floor"),
            should_skip_if_object_is_already_there=self.config.get_bool("should_skip_if_object_is_already_there", False)
        )

        add_properties = self.config.get_raw_dict("add_properties", {})
        if add_properties:
            config = Config({"add_properties": add_properties})
            loader_interface = LoaderInterface(config)
            loader_interface._set_properties(floors)