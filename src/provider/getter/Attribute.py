import numpy as np
import mathutils

from src.main.Provider import Provider
from src.utility.BlenderUtility import get_bounds


class Attribute(Provider):
    """

    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """

        :return:
        """
        # get objects
        objects = self.config.get_list("entities")
        # get parameter to look for
        param_defined = self.config.has_param("parameter")
        cp_param_defined = self.config.has_param("cp_parameter")
        if param_defined:
            look_for = self.config.get_string("parameter")
            cp_search = False
        elif cp_param_defined:
            look_for = self.config.get_string("cp_parameter")
            cp_search = True
        elif all([param_defined, cp_param_defined]) or all([not param_defined, not cp_param_defined]):
            raise RuntimeError("Please define only one out of two: `parameter` or `cp_parameter`!")

        raw_result = []
        for obj in objects:
            if hasattr(obj, look_for) and not cp_search:
                raw_result.append(getattr(obj, look_for))
            elif look_for in obj and cp_search:
                raw_result.append(obj[look_for])
            elif look_for == "bounding_box_centers":
                raw_result.append(mathutils.Vector(np.mean(get_bounds(obj), axis=0).tolist()))
            else:
                raise RuntimeError("Unknown parameter name: " + look_for)

        if self.config.has_param("output_type"):
            output_type = self.config.get_string("output_type")
            if self._check_compatibility(raw_result):
                if output_type == "sum":
                    ref_result = self._sum(raw_result)
                elif output_type == "avg":
                    ref_result = self._avg(raw_result)
                else:
                    raise RuntimeError("Unknown output_type: " + output_type)
            else:
                raise RuntimeError("Performing " + str(output_type) + " on " + str(look_for) + " type is not allowed!")
            result = ref_result
        else:
            result = raw_result

        return result

    def _check_compatibility(self, raw_result):
        """

        :param raw_result:
        :return:
        """
        return any([all(isinstance(item, mathutils.Vector) for item in raw_result),
                    all(isinstance(item, int) for item in raw_result),
                    all(isinstance(item, float) for item in raw_result)])

    def _sum(self, raw_result):
        """

        :return:
        """
        if isinstance(raw_result[0], mathutils.Vector):
            ref_result = mathutils.Vector([0, 0, 0])
        else:
            ref_result = 0
        for item in raw_result:
            ref_result += item

        return ref_result

    def _avg(self, raw_result):
        """

        :return:
        """
        ref_result = self._sum(raw_result)
        ref_result = ref_result/len(raw_result)

        return ref_result
