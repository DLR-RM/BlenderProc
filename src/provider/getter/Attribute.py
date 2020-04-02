import numpy as np
import mathutils

from src.main.Provider import Provider
from src.utility.BlenderUtility import get_bounds


class Attribute(Provider):
    """ Returns a value that is the result of selecting entities using getter.Entity Provider, getting the list of
        values of selected entities attributes/custom properties/custom-processed data based on the provided name of
        the parameter/custom property/custom function name, and of the optional operations on this list.


        Example 1: Get a list of locations of objects (which names match the pattern).

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

    .. csv-table::
        :header: "Parameter", "Description"

        "entities", "List of objects selected by the getter.Entity Provider. Type: list."
        "get", "Attribute/Custom property/custom function name on which the return value is based. Must be a valid "
               "name of selected entities' attribute/custom property, or a custom function name. Every entity selected "
               "must have this attribute, custom prop, or must be usable in a custom function, otherwise an exception "
               "will be thrown. Type: string."
               "In order to specify, what exactly one want to modify (e.g. attribute, custom property, etc.):"
               "For attribute: key of the pair must be a valid attribute name of the all selected entities."
               "For custom property: key of the pair must start with `cp_` prefix."
               "For calling custom function: key of the pair must start with `cf_` prefix. See table below for "
               "supported cf names."
        "transform_by", "Name of the operation to perform on the list of attributes/custom property/custom data values. "
                        "Type: string. Supported input types: (list of) int, float, mathutils.Vector. See below for "
                        "supported operation names."

        **Custom function names for `get` parameter**

    .. csv-table::
        :header: "Parameter", "Description"

        "cf_bounding_box_means", "Custom function name for `get` parameter. Invokes a chain of operations which "
                                 "returns a list of arithmetic means of coordinates of object aligned bounding boxes' "
                                 "of selected objects in world coordinates format."

        **Operation names for `transform_by` parameter**

    .. csv-table::
        :header: "Parameter", "Description"

        "sum", "Operation name. Returns the sum of all values of the input list."
        "avg", "Operation name. Returns the average value of all values of the input list. "

    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Selects objects, gets a list of appropriate values of objects' attributes, custom properties, or some
            processed custom data and optionally performs some operation of this list.

        :return: List of values (if only `get` was specified)
                 or a singular int, float, or mathutils.Vector (if some operation was applied).
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
                bb_mean = np.mean(get_bounds(obj), axis=0)
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

        return result

    def _check_compatibility(self, raw_result):
        """ Checks if the list of values contains appropriate data of int, float, or mathutils.Vector type.

        :param raw_result: list of selected objects' attribute/custom prop./or custom data values. Type: List
        :return: True if list is of homogeneous data type of int, float, or mathutils.Vector. False if not.
        """
        return any([all(isinstance(item, mathutils.Vector) for item in raw_result),
                    all(isinstance(item, int) for item in raw_result),
                    all(isinstance(item, float) for item in raw_result)])

    def _sum(self, raw_result):
        """ Sums up the values of the list.

        :return: The sum of all values of the input list.
        """
        if isinstance(raw_result[0], mathutils.Vector):
            ref_result = mathutils.Vector([0] * len(raw_result[0]))
        else:
            ref_result = 0
        for item in raw_result:
            ref_result += item

        return ref_result

    def _avg(self, raw_result):
        """ Sums up the values of the list and divides the sum by the amount of items in the list.

        :return: The average value of all values of the input list.
        """
        ref_result = self._sum(raw_result)
        ref_result = ref_result/float(len(raw_result))

        return ref_result
