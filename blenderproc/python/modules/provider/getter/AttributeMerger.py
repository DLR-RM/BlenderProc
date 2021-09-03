import mathutils 
import numpy as np

from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.modules.utility.Config import Config


class AttributeMerger(Provider):
    """
    Similarly to getter.Attribute Provider, getter.AttributeMerger returns the result of processing of the list of
    values, but the list is comprised of the return values of invoked providers. All return values in the list must
    comply with the requirements. See tables below for more info.

    Example 1: Get a mathutils.Vector which represents an average vector of two Uniform3d sampler return values

    .. code-block:: yaml

        {
          "provider": "getter.AttributeMerger",
          "elements": [
          {
            "provider": "sampler.Uniform3d",
            "min": [0, 0, 0],
            "max": [1, 1, 1]
          },
          {
            "provider": "sampler.Uniform3d",
            "min": [2, 2, 2],
            "max": [3, 3, 3]
          }
          ],
          "transform_by": "avg"
        }

    Example 2: Get a value which is a sum of a point sampled by sampler.Uniform3d, of an average location of all
    objects with names matching the pattern, and of a constant location.

    .. code-block:: yaml

        {
          "provider": "getter.AttributeMerger",
          "elements": [
          {
            "provider": "sampler.Uniform3d",
            "min": [0, 0, 0],
            "max": [1, 1, 1]
          },
          {
            "provider": "getter.Attribute",
            "entities": {
              "provider": "getter.Entity",
              "conditions": {
                "name": "Icosphere.*"
              }
            },
          "get": "location",
          "transform_by": "avg"
          },
            [1, 2, 3]
          ],
          "transform_by": "sum"
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - elements
          - List of user-configured Provider calls.
          - list
        * - transform_by
          - Name of the operation to perform on the list of Provider return values. See table below for supported
            operation names. 
          - string

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
        """ Returns the result of processing of the list of values. """
        transform_by = self.config.get_string("transform_by")
        elements = self.config.get_list("elements")

        raw_result = []
        for element in elements:
            element_conf = Config({"element": element})
            if isinstance(element, list):
                raw_result.append(element_conf.get_vector3d("element"))
            else:
                raw_result.append(element_conf.get_raw_value("element"))

        if len(raw_result) > 0:
            if self._check_compatibility(raw_result):
                if transform_by == "sum":
                    ref_result = self._sum(raw_result)
                elif transform_by == "avg":
                    ref_result = self._avg(raw_result)
                else:
                    raise RuntimeError("Unknown 'transform_by' operation: " + transform_by)
            else:
                raise RuntimeError("Provider output types don't match. All must either int, float, or mathutils.Vector.")
        else:
            raise RuntimeError("List of resulting values of `elements` is empty. Please, check Provider configuration.")

        return ref_result

    @staticmethod
    def _check_compatibility(raw_result):
        """ Checks if the list of values contains appropriate data of int/float, or mathutils.Vector type.

        :param raw_result: list of provider output values. Type: List
        :return: True if list is of of int (and/or) float, or mathutils.Vector data type. False if not. Type: bool.
        """
        return any([all(isinstance(item, (mathutils.Vector, np.ndarray)) for item in raw_result),
                    all(isinstance(item, (int, float)) for item in raw_result)])

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
