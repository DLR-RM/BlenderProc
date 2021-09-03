import mathutils
import numpy as np

import blenderproc.python.utility.Utility as Utility
from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.modules.main.GlobalStorage import GlobalStorage

class Config:
    # Used in get_* functions to denote that no fallback value is specified
    no_fallback = object()

    def __init__(self, data):
        self.data = data

    def is_empty(self):
        """ Checks if the config contains no parameters.

        :return: True, if the config is empty
        """
        return len(self.data) == 0

    def has_param(self, name, block=None):
        """ Check if parameter is defined in config

        :param name: The name of the parameter. "/" can be used to represent nested parameters \
                     (e.q. "render/iterations" results in ["render"]["iterations"]
        :param block: A dict containing the configuration. If none, the whole data of this config object will be used.
        :return: True if parameter exists, False if not
        """

        if block is None:
            block = self.data

        if "/" in name:
            delimiter_pos = name.find("/")
            block_name = name[:delimiter_pos]
            if block_name in block and type(block[block_name]) is dict:
                return self.has_param(name[delimiter_pos + 1:], block[block_name])
        else:
            return name in block
            
        return False
            
    def _get_value(self, name, block=None, allow_invoke_provider=False, global_check=True):
        """ Returns the value of the parameter with the given name inside the given block.

        Basically just a recursive dict lookup, making sure the parameter exists, otherwise an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param block: A dict containing the configuration. If none, the whole data of this config object will be used.
        :param allow_invoke_provider: If set to True, then a provider is automatically invoked if the parameter value is a dict.
        :return: The value of the parameter.
        """
        if block is None:
            block = self.data

        if "/" in name:
            delimiter_pos = name.find("/")
            block_name = name[:delimiter_pos]
            if block_name in block and type(block[block_name]) is dict:
                return self._get_value(name[delimiter_pos + 1:], block[block_name], allow_invoke_provider)
            else:
                raise NotFoundError("No such configuration block '" + block_name + "'!")
        else:
            if name in block:

                # Check for whether a provider should be invoked
                if allow_invoke_provider and type(block[name]) is dict:
                    block[name] = Utility.Utility.build_provider_based_on_config(block[name])

                # If the parameter is set to a provider object, call the provider to return the parameter value
                if isinstance(block[name], Provider):
                    return block[name].run()
                else:
                    return block[name]
            elif global_check and GlobalStorage.has_param(name):
                # this might also throw an NotFoundError
                return GlobalStorage.get_global_config()._get_value(name, None, allow_invoke_provider, global_check=False)
            else:
                raise NotFoundError("No such configuration '" + name + "'!")
            
    def _get_value_with_fallback(self, name, fallback=no_fallback, allow_invoke_provider=False):
        """ Returns the value of the given parameter with the given name.

        If the parameter does not exist, the given fallback value is returned.
        If Config.no_fallback as fallback is given, an error is thrown in such a case.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value.
        :param allow_invoke_provider: If set to True, then a provider is automatically invoked if the parameter value is a dict.
        :return: The value of the parameter.
        """
        try:
            return self._get_value(name, None, allow_invoke_provider)
        except NotFoundError:
            if fallback != Config.no_fallback:
                return fallback
            else:
                raise

    def get_raw_dict(self, name, fallback=no_fallback):
        """ Returns the complete dict stored at the given parameter path.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The dict.
        """
        return self._get_value_with_fallback(name, fallback)

    def get_raw_value(self, name, fallback=no_fallback):
        """ Returns the raw value stored at the given parameter path.
        If a provider is specified at the given parameter path, then the provider is first invoked and the result is directly returned.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The raw value.
        """
        return self._get_value_with_fallback(name, fallback, True)

    def get_int(self, name, fallback=no_fallback):
        """ Returns the integer value stored at the given parameter path.

        If the value is no integer, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The integer value.
        """
        value = self._get_value_with_fallback(name, fallback, True)
        try:
            return int(value) if value is not None else value
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to int!")

    def get_bool(self, name, fallback=no_fallback):
        """ Returns the boolean value stored at the given parameter path.

        If the value is no boolean, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The boolean value.
        """
        value = self._get_value_with_fallback(name, fallback, True)
        try:
            return bool(value) if value is not None else value
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to bool!")

    def get_float(self, name, fallback=no_fallback):
        """ Returns the float value stored at the given parameter path.

        If the value is no float, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The float value.
        """
        value = self._get_value_with_fallback(name, fallback, True)
        try:
            return float(value) if value is not None else value
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to float!")

    def get_string(self, name, fallback=no_fallback):
        """ Returns the string value stored at the given parameter path.

        If the value is no string, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The string value.
        """
        value = self._get_value_with_fallback(name, fallback, True)
        try:
            return str(value) if value is not None else value
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to string!")

    def get_list(self, name, fallback=no_fallback):
        """ Returns the list stored at the given parameter path.

        If the value is no list, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The list.
        """
        value = self._get_value_with_fallback(name, fallback, True)

        if value is not None:
            if isinstance(value, (mathutils.Vector, np.ndarray)):
                value = list(value)

            if not isinstance(value, list):
                raise TypeError("Cannot convert '" + str(value) + "' to list!")

        return value

    def get_vector(self, name, fallback=no_fallback, dimensions=None):
        """ Returns the vector stored at the given parameter path.

        If the value cannot be converted to mathutils.Vector, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :param dimensions: If not None, specifies the required number of dimensions. If the configured vector has not exactly this number of dimensions, an error is thrown.
        :return: The vector.
        """
        value = self.get_list(name, fallback)

        if value is not None:
            if dimensions is not None and len(value) != dimensions:
                raise TypeError(str(value) + "' must have exactly " + str(dimensions) + " dimensions!")

            try:
                value = mathutils.Vector(value)
            except ValueError:
                raise TypeError("Cannot convert '" + str(value) + "' to a mathutils.Vector!")

        return value

    def get_vector2d(self, name, fallback=no_fallback):
        """ Returns the vector stored at the given parameter path.

        If the value cannot be converted to an mathutils.Vector, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The vector.
        """
        return self.get_vector(name, fallback, 2)

    def get_vector3d(self, name, fallback=no_fallback):
        """ Returns the vector stored at the given parameter path.

        If the value cannot be converted to an mathutils.Vector, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The vector.
        """
        return self.get_vector(name, fallback, 3)

    def get_vector4d(self, name, fallback=no_fallback):
        """ Returns the vector stored at the given parameter path.

        If the value cannot be converted to an mathutils.Vector, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The vector.
        """
        return self.get_vector(name, fallback, 4)

    def get_matrix(self, name, fallback=no_fallback, dimensions=None):
        """ Returns the matrix stored at the given parameter path.

        If the value cannot be converted to mathutils matrix, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :param dimensions: If not None, specifies the required number of dimensions. If the configured matrix has not exactly this dimensional, an error is thrown.
        :return: The matrix.
        """
        value = self.get_raw_value(name, fallback)

        if value is not None:
            if dimensions is not None and (len(value) != dimensions or not all(len(item) == dimensions for item in value)):
                raise TypeError(str(value) + "' must be exactly " + str(dimensions) + "x" + str(dimensions) + "-dimensional!")

            try:
                value = mathutils.Matrix(value)
            except ValueError:
                raise TypeError("Cannot convert '" + str(value) + "' to a mathutils matrix!")

        return value

    def get_matrix_2x2(self, name, fallback=no_fallback):
        """ Returns the 2x2 matrix stored at the given parameter path.

        If the value cannot be converted to an mathutils matrix, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The matrix.
        """
        return self.get_matrix(name, fallback, 2)

    def get_matrix_3x3(self, name, fallback=no_fallback):
        """ Returns the 3x3 matrix stored at the given parameter path.

        If the value cannot be converted to an mathutils matrix, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The matrix.
        """
        return self.get_matrix(name, fallback, 3)

    def get_matrix_4x4(self, name, fallback=no_fallback):
        """ Returns the 3x3 matrix stored at the given parameter path.

        If the value cannot be converted to an mathutils matrix, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist. If Config.no_fallback is given, an exception is thrown in such cases.
        :return: The matrix.
        """
        return self.get_matrix(name, fallback, 4)


class NotFoundError(Exception):
    pass
