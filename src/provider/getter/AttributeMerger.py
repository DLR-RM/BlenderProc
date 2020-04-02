import mathutils

from src.main.Provider import Provider
from src.utility.Config import Config


class AttributeMerger(Provider):
    """ Similarly to getter.Attribute Provider, getter.AttributeMerger returns the result of processing of the list of
        values, but the list is comprised of the return values of invoked providers. All return values in the list must
        comply with the requirements. See tables below for more info.

        Example 1: Get a mathutils.Vector which represents an average vector of two Uniform3d sampler return values

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

        Example 2: Get a value which is a sum of a point sampled by sampler.Uniform3d and an average location of all
                   objects with names matching the pattern.

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
          }
          ],
          "transform_by": "sum"
        }

        **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "elements", "List of user-configured Provider calls. Type: list."
        "transform_by", "Name of the operation to perform on the list of Provider return values. Type: string. "
                        "Supported input types: (list of) int, float, mathutils.Vector. See below for supported "
                        "operation names."

        **Operation names for `transform_by` parameter**

    .. csv-table::
        :header: "Parameter", "Description"

        "sum", "Operation name. Returns the sum of all values of the input list."
        "avg", "Operation name. Returns the average value of all values of the input list."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """

        :return:
        """
        transform_by = self.config.get_string("transform_by")
        elements = self.config.get_list("elements")

        raw_result = []
        for element in elements:
            if "provider" in element:
                element_conf = Config({"element": element})
                raw_result.append(element_conf.get_raw_value("element"))
            else:
                raise RuntimeError("Each cell of the of `elements` list must contain a configured Provider call.")

        if self._check_compatibility(raw_result):
            if transform_by == "sum":
                ref_result = self._sum(raw_result)
            elif transform_by == "avg":
                ref_result = self._avg(raw_result)
            else:
                raise RuntimeError("Unknown 'transform_by' operation: " + transform_by)
        else:
            raise RuntimeError("Provider output types don't match. All must either int, float, or mathutils.Vector.")

        return ref_result

    def _check_compatibility(self, raw_result):
        """ Checks if the list of values contains appropriate data of int, float, or mathutils.Vector type.

        :param raw_result: list of provider output values. Type: List
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
