import mathutils


class Config:

    def __init__(self, data):
        self.data = data

    def _has_param(self, name, block=None):
        """ Check if parameter is defined in config 
        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param block: A dict containing the configuration. If none, the whole data of this config object will be used.
        :return: True if parameter exists, False if not
        """

        if block is None:
            block = self.data

        if "/" in name:
            delimiter_pos = name.find("/")
            block_name = name[:delimiter_pos]
            if block_name in block and type(block[block_name]) is dict:
                return self._has_param(name[delimiter_pos + 1:], block[block_name])
        else:
            return name in block
            
        return False
            
    def _get_value(self, name, block=None):
        """ Returns the value of the parameter with the given name inside the given block.

        Basically just a recursive dict lookup, making sure the parameter exists, otherwise an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param block: A dict containing the configuration. If none, the whole data of this config object will be used.
        :return: The value of the parameter.
        """
        if block is None:
            block = self.data

        if "/" in name:
            delimiter_pos = name.find("/")
            block_name = name[:delimiter_pos]
            if block_name in block and type(block[block_name]) is dict:
                return self._get_value(name[delimiter_pos + 1:], block[block_name])
            else:
                raise NotFoundError("No such configuration block '" + block_name + "'!")
        else:
            if name in block:
                return block[name]
            else:
                raise NotFoundError("No such configuration '" + name + "'!")
            
    def _get_value_with_fallback(self, name, fallback=None):
        """ Returns the value of the given parameter with the given name.

        If the parameter does not exist, the given fallback value is returned.
        If no fallback is given, an error is thrown in such a case.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value.
        :return: The value of the parameter.
        """
        try:
            return self._get_value(name)
        except NotFoundError:
            if fallback is not None:
                return fallback
            else:
                raise

    def get_raw_dict(self, name, fallback=None):
        """ Returns the complete dict stored at the given parameter path.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The dict.
        """
        return self._get_value_with_fallback(name, fallback)

    def get_int(self, name, fallback=None):
        """ Returns the integer value stored at the given parameter path.

        If the value is no integer, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The integer value.
        """
        value = self._get_value_with_fallback(name, fallback)
        try:
            return int(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to int!")

    def get_bool(self, name, fallback=None):
        """ Returns the boolean value stored at the given parameter path.

        If the value is no boolean, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The boolean value.
        """
        value = self._get_value_with_fallback(name, fallback)
        try:
            return bool(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to bool!")

    def get_float(self, name, fallback=None):
        """ Returns the float value stored at the given parameter path.

        If the value is no float, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The float value.
        """
        value = self._get_value_with_fallback(name, fallback)
        try:
            return float(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to float!")

    def get_string(self, name, fallback=None):
        """ Returns the string value stored at the given parameter path.

        If the value is no string, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The string value.
        """
        value = self._get_value_with_fallback(name, fallback)
        try:
            return str(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to string!")

    def get_list(self, name, fallback=None):
        """ Returns the list stored at the given parameter path.

        If the value is no list, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The list.
        """
        value = self._get_value_with_fallback(name, fallback)
        if not isinstance(value, list):
            raise TypeError("Cannot convert '" + str(value) + "' to list!")

        return value

    def get_vector(self, name, fallback=None, dimensions=None):
        """ Returns the vector stored at the given parameter path.

        If the value cannot be converted to mathutils vector, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :param dimensions: If not None, specifies the required number of dimensions. If the configured vector has not exactly this number of dimensions, an error is thrown.
        :return: The vector.
        """
        value = self.get_list(name, fallback)

        if dimensions is not None and len(value) != dimensions:
            raise TypeError(str(value) + "' must have exactly " + str(dimensions) + " dimensions!")

        try:
            value = mathutils.Vector(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to a mathutils vector!")

        return value

    def get_vector2d(self, name, fallback=None):
        """ Returns the vector stored at the given parameter path.

        If the value cannot be converted to an mathutils vector, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The vector.
        """
        return self.get_vector(name, fallback, 2)

    def get_vector3d(self, name, fallback=None):
        """ Returns the vector stored at the given parameter path.

        If the value cannot be converted to an mathutils vector, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The vector.
        """
        return self.get_vector(name, fallback, 3)

    def get_vector4d(self, name, fallback=None):
        """ Returns the vector stored at the given parameter path.

        If the value cannot be converted to an mathutils vector, an error is thrown.

        :param name: The name of the parameter. "/" can be used to represent nested parameters (e.q. "render/iterations" results in ["render"]["iterations]
        :param fallback: The fallback value, returned if the parameter does not exist.
        :return: The vector.
        """
        return self.get_vector(name, fallback, 4)

class NotFoundError(Exception):
    pass