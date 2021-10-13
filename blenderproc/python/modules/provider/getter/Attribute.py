import mathutils
import numpy as np

from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.types.MeshObjectUtility import MeshObject


class Attribute(Provider):
    """
    Returns a value that is the result of selecting entities using getter.Entity Provider, getting the list of
    values of selected entities' attributes/custom properties/custom-processed data, and of the optional operations
    on this list.

    Example 1: Get a list of locations of objects (which names match the pattern).

    .. code-block:: yaml

        {
          "provider": "getter.Attribute",
          "entities": {
            "provider": "getter.Entity",
            "conditions": {
              "name": "Icosphere.*"
            }
          },
          "get": "location"
          # add "transform_by": "sum" to get one value that represents the sum of those locations.
        }

    Example 2: Get a list of custom property "id" values of objects (which "physics" cp value is True).

    .. code-block:: yaml

        {
          "provider": "getter.Attribute",
          "entities": {
            "provider": "getter.Entity",
            "conditions": {
              "cp_physics": "True"
            }
          },
          "get": "cp_id"
        }

    Example 3: Get a list of mean coordinates of objects (which name matches the pattern) bounding boxes.

    .. code-block:: yaml

        {
          "provider": "getter.Attribute",
          "entities": {
            "provider": "getter.Entity",
            "conditions": {
              "name": "Cube.*"
            }
          },
          "get": "cf_bounding_box_means"
          # add "transform_by": "avg" to get one value that represents the average coordinates of those bounding boxes
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - entities
          - List of objects selected by the getter.Entity Provider.
          - list
        * - get
          - Attribute/Custom property/custom function name on which the return value is based. Must be a valid name
            of selected entities' attribute/custom property, or a custom function name. Every entity selected must
            have this attribute, custom prop, or must be usable in a custom function, otherwise an exception will be
            thrown. " In order to specify, what exactly one wants to get (e.g. attribute, custom property, etc.):
            For attribute: key of the pair must be a valid attribute name of the all selected entities. For custom
            property: key of the pair must start with `cp_` prefix. For calling custom function: key of the pair
            must start with `cf_` prefix. See table below for supported custom function names.
          - string
        * - transform_by
          - Name of the operation to perform on the list of attributes/custom property/custom data values. See table
            below for supported operation names.
          - string.
        * - index
          - If set, after the conditions are applied only the corresponding value of entity with the specified index
            is returned. 
          - int

    **Custom functions**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cf_bounding_box_means
          - Custom function name for `get` parameter. Invokes a chain of operations which returns a list of
            arithmetic means of coordinates of object aligned bounding boxes' of selected objects in world
            coordinates format. (return).
          - list

    **Operations**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - sum
          - Returns the sum of all values of the input list. (return).
          - float
        * - avg
          - Returns the average value of all values of the input list. (return).
          - float
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Selects objects, gets a list of appropriate values of objects' attributes, custom properties, or some
            processed custom data and optionally performs some operation of this list.

        :return: List of values (only if `get` was specified or a custom function was called)
                 or a singular int, float, or mathutils.Vector value (if some operation was applied).
        """
        objects = self.config.get_list("entities")
        look_for = self.config.get_string("get")

        cp_search = False
        cf_search = False
        if look_for.startswith('cp_'):
            look_for = look_for[3:]
            cp_search = True
        elif look_for.startswith('cf_'):
            look_for = look_for[3:]
            cf_search = True

        raw_result = []
        for obj in objects:
            if hasattr(obj, look_for) and not cp_search:
                raw_result.append(getattr(obj, look_for))
            elif look_for in obj and cp_search:
                raw_result.append(obj[look_for])
            elif look_for == "bounding_box_means" and cf_search:
                bb_mean = np.mean(MeshObject(obj).get_bound_box(), axis=0)
                raw_result.append(mathutils.Vector(bb_mean))
            else:
                raise RuntimeError("Unknown parameter name: " + look_for)

        if self.config.has_param("transform_by"):
            transform_by = self.config.get_string("transform_by")
            if self._check_compatibility(raw_result):
                if transform_by == "sum":
                    ref_result = self._sum(raw_result)
                elif transform_by == "avg":
                    ref_result = self._avg(raw_result)
                else:
                    raise RuntimeError("Unknown transform_by: " + transform_by)
            else:
                raise RuntimeError("Performing " + str(transform_by) + " on " + str(look_for) + " " +
                                   str(type(raw_result[0])) + " type is not allowed!")
            result = ref_result
        else:
            result = raw_result

        if self.config.has_param("index"):
            result = result[self.config.get_int("index")]

        return result

    def _check_compatibility(self, raw_result):
        """ Checks if the list of values contains appropriate data of int, float, or mathutils.Vector type.

        :param raw_result: list of selected objects' attribute/custom prop./or custom data values. Type: List
        :return: True if list is of int (and or) float, or mathutils.Vector data type. False if not. Type: bool.
        """
        return any([all(isinstance(item, mathutils.Vector) for item in raw_result),
                    all(isinstance(item, (float, int)) for item in raw_result)])

    def _sum(self, raw_result):
        """ Sums up the values of the list.

        :return: The sum of all values of the input list.
        """
        ref_result = raw_result[0].copy()
        for item in raw_result[1:]:
            ref_result += item

        return ref_result

    def _avg(self, raw_result):
        """ Sums up the values of the list and divides the sum by the amount of items in the list.

        :return: The average value of all values of the input list.
        """
        ref_result = self._sum(raw_result)
        ref_result = ref_result/float(len(raw_result))

        return ref_result
