from typing import Any

from src.utility.StructUtility import Struct
import mathutils
import re

class StructFilter:
    @staticmethod
    def _check_list_has_length_one(elements: [Any]) -> Any:
        """ Checks if the given list only contains one element and returns it.

        :param elements: The list of elements to check.
        :return: The one element of the list.
        """
        if len(elements) > 1:
            raise Exception("More than one element with the given condition has been found.")
        if len(elements) == 0:
            raise Exception("No element with the given condition has been found.")
        return elements[0]

    @staticmethod
    def _check_equality(attr_value: Any, filter_value: Any, regex: bool = False) -> bool:
        """ Checks whether the two values are equal.

        :param attr_value: The first value.
        :param filter_value: The second value.
        :param regex: If True, string values will be matched via regex.
        :return: True, if the two values are equal.
        """
        # Optionally cast type
        if isinstance(attr_value, mathutils.Vector):
            filter_value = mathutils.Vector(filter_value)
        elif isinstance(attr_value, mathutils.Euler):
            filter_value = mathutils.Euler(filter_value)
        elif isinstance(attr_value, mathutils.Color):
            filter_value = mathutils.Color(filter_value)

        # If desired do regex matching for strings
        if isinstance(attr_value, str) and regex:
            return re.fullmatch(filter_value, attr_value)
        else:
            return filter_value == attr_value

    @staticmethod
    def by_attr(elements: [Struct], attr_name: str, value: Any, regex: bool = False) -> [Struct]:
        """ Returns all elements from the given list whose specified attribute has the given value.

        :param elements: A list of elements.
        :param attr_name: The name of the attribute to look for.
        :param value: The value the attribute should have.
        :param regex: If True, string values will be matched via regex.
        :return: The elements from the given list that match the given value at the specified attribute.
        """
        return list(filter(lambda struct: StructFilter._check_equality(struct.get_attr(attr_name), value, regex), elements))

    @staticmethod
    def one_by_attr(elements: [Struct], attr_name: str, value: Any, regex: bool = False) -> Struct:
        """ Returns the one element from the given list whose specified attribute has the given value.

        An error is thrown is more than one or no element has been found.

        :param elements: A list of elements.
        :param attr_name: The name of the attribute to look for.
        :param value: The value the attribute should have.
        :param regex: If True, string values will be matched via regex.
        :return: The one element from the given list that matches the given value at the specified attribute.
        """
        elements = StructFilter.by_attr(elements, attr_name, value, regex)
        return StructFilter._check_list_has_length_one(elements)

    @staticmethod
    def by_cp(elements: [Struct], cp_name: str, value: Any, regex: bool = False) -> [Struct]:
        """  Returns all elements from the given list whose specified custom property has the given value.

        :param elements: A list of elements.
        :param cp_name: The name of the custom property to look for.
        :param value: The value the custom property should have.
        :param regex: If True, string values will be matched via regex.
        :return: The elements from the given list that match the given value at the specified custom property.
        """
        return list(filter(lambda struct: struct.has_cp(cp_name) and StructFilter._check_equality(struct.get_cp(cp_name), value, regex), elements))

    @staticmethod
    def one_by_cp(elements: [Struct], cp_name: str, value: Any, regex: bool = False) -> Struct:
        """ Returns the one element from the given list whose specified custom property has the given value.

        An error is thrown is more than one or no element has been found.

        :param elements: A list of elements.
        :param cp_name: The name of the custom property to look for.
        :param value: The value the custom property should have.
        :param regex: If True, string values will be matched via regex.
        :return: The one element from the given list that matches the given value at the specified custom property.
        """
        elements = StructFilter.by_cp(elements, cp_name, value, regex)
        return StructFilter._check_list_has_length_one(elements)

    @staticmethod
    def by_attr_in_interval(elements: [Struct], attr_name: str, min_value: Any = None, max_value: Any = None) -> [Struct]:
        """ Returns all elements from the given list whose specified attribute has a value in the given interval.

        :param elements: A list of elements.
        :param attr_name: The name of the attribute to look for.
        :param min_value: The minimum value of the interval.
        :param max_value: The maximum value of the interval.
        :return: The elements from the given list that match the given value at the specified attribute.
        """
        return list(filter(lambda struct: (min_value is None or min_value < struct.get_attr(attr_name)) and (max_value is None or max_value > struct.get_attr(attr_name)), elements))

    @staticmethod
    def by_attr_outside_interval(elements: [Struct], attr_name: str, min_value: Any = None, max_value: Any = None) -> [Struct]:
        """ Returns all elements from the given list whose specified attribute has a value outside the given interval.

        :param elements: A list of elements.
        :param attr_name: The name of the attribute to look for.
        :param min_value: The minimum value of the interval.
        :param max_value: The maximum value of the interval.
        :return: The elements from the given list that match the given value at the specified attribute.
        """
        in_interval = StructFilter.by_attr_in_interval(elements, attr_name, min_value, max_value)
        return [e for e in elements if e not in in_interval]
